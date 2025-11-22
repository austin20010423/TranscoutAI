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


def extract_entities_with_gpt4(user_query: str) -> Tuple[List[str], str]:
    """Use OpenAI API to extract tags and summary."""
    prompt = f"""
    You are an AI that extracts structured entities from a natural language query.

    Your task:
    - Identify key **tags** (short keywords/topics such as ["AI", "bug", "TechCrunch"])
    - Produce a **summary** (1–2 sentences capturing what the user wants)

    Return JSON only, with this structure:
    {{
    "tags": [string],
    "summary": string
    }}

    Examples:
    ---
    Query: "Show me recent AI-related TechCrunch tickets"
    Output: {{ "tags": ["AI", "TechCrunch"], "summary": "User wants recent TechCrunch tickets about AI." }}
    ---
    Query: "Find bug reports mentioning payment errors"
    Output: {{ "tags": ["bug", "payment"], "summary": "User wants tickets about payment-related bugs." }}
    ---
    Query: "Tickets about UX improvements and AI suggestions"
    Output: {{ "tags": ["UX", "AI"], "summary": "User asks for tickets discussing UX and AI improvements." }}
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
        data = {"tags": [], "summary": user_query}

    tags = data.get("tags", [])
    summary = data.get("summary", user_query)
    return tags, summary


# ---------------------------------------------------------------------
# Neo4j Semantic Search + Tag Filtering (inside Neo4j)
# ---------------------------------------------------------------------
def semantic_search_with_tag_filter_in_neo4j(
    tx,
    query_vector: List[float],
    tags: List[str],
    semantic_limit: int = 200,
    top_k: int = 10
):
    """
    Perform semantic similarity search + tag filtering inside Neo4j.
    If tags are provided, only tickets that have at least one of those tags are kept.
    """
    cypher = """
    WITH $qv AS qv, $tags AS tags
    MATCH (t:Entity {type:'ticket'})
    WHERE t.title_embedding IS NOT NULL
    OPTIONAL MATCH (t)-[:HAS_TAG]->(tag:Entity)
    WITH t, qv, tags, collect(DISTINCT tag.name) AS tag_names,
        vector.similarity.cosine(qv, t.title_embedding) AS sim
    WHERE size(tags) = 0 OR any(tag IN tag_names WHERE toLower(tag) IN [tagName IN tags | toLower(tagName)])
    WITH t, sim, tag_names
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

    return tx.run(cypher, qv=query_vector, tags=tags, top_k=top_k).data()


# ---------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------
def text_query_to_results(user_query: str,
                          semantic_limit: int = 10,
                          semantic_top_k: int = 10,
                          top_n: int = 5) -> Dict[str, Any]:
    print(f"\n💬 USER QUERY: {user_query}")

    tags, summary = extract_entities_with_gpt4(user_query)
    print("🎯 Summary:", summary)
    print("🏷️ Tags:", tags)

    query_vector = embed_e5_query(summary)

    with driver.session() as s:
        results = s.execute_read(
            semantic_search_with_tag_filter_in_neo4j,
            query_vector,
            tags,
            semantic_limit,
            semantic_top_k
        )

    if not results:
        return {"answer": "No matching tickets found.", "results": []}

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



