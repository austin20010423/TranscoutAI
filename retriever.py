from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from transformers import AutoTokenizer, AutoModel
import torch, json, config
from openai import OpenAI


# ---------------------------------------------------------------------
# Load E5 Embedding Model
# ---------------------------------------------------------------------
print(f"Loading E5 model: {config.E5_MODEL_NAME}")
_tokenizer = AutoTokenizer.from_pretrained(config.E5_MODEL_NAME)
_model = AutoModel.from_pretrained(config.E5_MODEL_NAME)

@torch.no_grad()
def embed_e5_query(text: str) -> List[float]:
    """Return normalized E5 embedding for a user query."""
    text = text.strip()
    if not text.lower().startswith("query:"):
        text = "query: " + text
    inputs = _tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = _model(**inputs)
    emb = outputs.last_hidden_state.mean(dim=1)
    emb = torch.nn.functional.normalize(emb, p=2, dim=1)
    return emb[0].cpu().tolist()

driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))

client = OpenAI(api_key=config.OPENAI_API_KEY)


def extract_entities_with_gpt4(user_query: str) -> Tuple[List[str], List[str], List[str], str]:
    """Use OpenAI API to extract tags, locations, sources, and summary."""
    prompt = f"""
    You are an AI that extracts structured entities from a natural language query.

    Your task:
    - Identify key **tags** (short keywords/topics such as ["AI", "bug", "TechCrunch"])
    - Identify **locations** (cities, countries, regions like ["New York", "Texas", "USA"])
    - Identify **sources** (specific data sources if mentioned, e.g., ["TechCrunch", "GitHub"])
    - Produce a **summary** (1–2 sentences capturing what the user wants)

    Return JSON only, with this structure:
    {{
    "tags": [string],
    "locations": [string],
    "sources": [string],
    "summary": string
    }}

    Examples:
    ---
    Query: "Show me recent AI-related TechCrunch tickets in New York"
    Output: {{ "tags": ["AI"], "locations": ["New York"], "sources": ["TechCrunch"], "summary": "User wants recent TechCrunch tickets about AI in New York." }}
    ---
    Query: "Find bug reports mentioning payment errors"
    Output: {{ "tags": ["bug", "payment"], "locations": [], "sources": [], "summary": "User wants tickets about payment-related bugs." }}
    ---
    Query: "Startup companies in Texas from GitHub"
    Output: {{ "tags": ["Startup"], "locations": ["Texas"], "sources": ["GitHub"], "summary": "User asks for startup companies in Texas found on GitHub." }}
    ---

    Now analyze this query:
    Query: "{user_query}"
    Output JSON:
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
    except Exception as e:
        print("⚠️ GPT extraction failed:", e)
        data = {"tags": [], "locations": [], "sources": [], "summary": user_query}

    tags = data.get("tags", [])
    locations = data.get("locations", [])
    sources = data.get("sources", [])
    summary = data.get("summary", user_query)
    return tags, locations, sources, summary


# ---------------------------------------------------------------------
# Neo4j Semantic Search + Tag Filtering (inside Neo4j)
# ---------------------------------------------------------------------
def semantic_search_with_tag_filter_in_neo4j(
    tx,
    query_vector: List[float],
    tags: List[str],
    locations: List[str],
    sources: List[str],
    semantic_limit: int = 200,
    top_k: int = 10
):
    """
    Perform hybrid search:
    1. If filters (tags, locations, sources) are present -> Try Filtered Exact Search (KNN).
    2. If Filtered Search returns NO results -> Fallback to Vector Index (ANN).
    3. If NO filters -> Use Vector Index (ANN).
    """
    
    # Define queries
    vector_index_cypher = """
        CALL db.index.vector.queryNodes('ticket_title_embedding', $top_k, $qv)
        YIELD node AS t, score AS sim
        
        // Get full ticket context
        OPTIONAL MATCH (t)-[r]->(n:Entity)
        WITH t, sim, collect({rel: type(r), node: n}) AS related
        
        // Extract tags for consistency in return format
        OPTIONAL MATCH (t)-[:HAS_TAG]->(tag:Entity)
        WITH t, sim, related, collect(tag.name) AS tags
        
        RETURN
        t.ticket_id AS ticket_id,
        t.title AS title,
        t.type AS type,
        tags,
        sim,
        [x IN related | {
            relationship: x.rel,
            node_type: x.node.type,
            node_props: properties(x.node)
        }] AS relationships
    """

    filtered_cypher = """
        WITH $qv AS qv, $tags AS tags, $locations AS locations, $sources AS sources
        MATCH (t:Entity {type:'ticket'})
        WHERE t.title_embedding IS NOT NULL

        // 1. Tag Filtering
        OPTIONAL MATCH (t)-[:HAS_TAG]->(tag:Entity)
        WITH t, qv, tags, locations, sources, collect(DISTINCT tag.name) AS tag_names
        WHERE size(tags) = 0 OR any(tag IN tag_names WHERE toLower(tag) IN [tagName IN tags | toLower(tagName)])

        // 2. Location Filtering (via Metadata)
        OPTIONAL MATCH (t)-[:HAS_METADATA]->(meta:Entity)
        WITH t, qv, tags, locations, sources, tag_names, meta
        WHERE size(locations) = 0 OR (meta.location IS NOT NULL AND any(loc IN locations WHERE toLower(meta.location) CONTAINS toLower(loc)))

        // 3. Source Filtering
        OPTIONAL MATCH (t)-[:HAS_SOURCE]->(source:Entity)
        WITH t, qv, tags, locations, sources, tag_names, meta, source
        WHERE size(sources) = 0 OR (source.name IS NOT NULL AND any(src IN sources WHERE toLower(source.name) CONTAINS toLower(src)))

        // 4. Similarity Calculation
        WITH t, qv, tag_names,
             vector.similarity.cosine(qv, t.title_embedding) AS sim
        ORDER BY sim DESC
        LIMIT $top_k

        // Get full ticket context
        OPTIONAL MATCH (t)-[r]->(n:Entity)
        WITH t, sim, tag_names, collect({rel: type(r), node: n}) AS related
        RETURN
        t.ticket_id AS ticket_id,
        t.title AS title,
        t.type AS type,
        tag_names AS tags,
        sim,
        [x IN related | {
            relationship: x.rel,
            node_type: x.node.type,
            node_props: properties(x.node)
        }] AS relationships
    """

    # Logic
    has_filters = bool(tags or locations or sources)
    results = []

    if has_filters:
        print("🔍 Using Filtered Exact Search (KNN)...")
        results = tx.run(filtered_cypher, qv=query_vector, tags=tags, locations=locations, sources=sources, top_k=top_k).data()
        
        if not results:
            print("⚠️ No results found with filters. Falling back to Vector Index (ANN)...")
            results = tx.run(vector_index_cypher, qv=query_vector, top_k=top_k).data()
    else:
        print("⚡ Using Vector Index (ANN) for search...")
        results = tx.run(vector_index_cypher, qv=query_vector, top_k=top_k).data()

    return results


# ---------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------
def text_query_to_results(user_query: str,
                          semantic_limit: int = 10,
                          semantic_top_k: int = 10,
                          top_n: int = 5) -> Dict[str, Any]:
    print(f"\n💬 USER QUERY: {user_query}")

    tags, locations, sources, summary = extract_entities_with_gpt4(user_query)
    print("🎯 Summary:", summary)
    print("🏷️ Tags:", tags)
    print("📍 Locations:", locations)
    print("📡 Sources:", sources)

    query_vector = embed_e5_query(summary)

    with driver.session() as s:
        results = s.execute_read(
            semantic_search_with_tag_filter_in_neo4j,
            query_vector,
            tags,
            locations,
            sources,
            semantic_limit,
            semantic_top_k
        )

    if not results:
        return []

    top_results = results[:top_n]

    parsed = []
    for i, r in enumerate(top_results):
        ticket = {
            "rank": i + 1,
            "ticket_id": r["ticket_id"],
            "title": r["title"],
            "type": r["type"],
            "similarity": round(r["sim"], 4),
            "tags": r["tags"],
            "relationships": r["relationships"]
        }
        parsed.append(ticket)


    return parsed


# ---------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------
if __name__ == "__main__":
    query = "Show me recent AI-related startup company"
    result = text_query_to_results(query)

    print(result[0])



