import os, json, uuid
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
import time
from tqdm import tqdm

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser

import config
import dataOrganizer
from Data_Scraping import data_github, data_RSS


# -------------------------------
# Configuration
# -------------------------------
uri = config.NEO4J_URI
user = config.NEO4J_USER
password = config.NEO4J_PASSWORD

llm_model = config.OPEN_MODEL
embedding_model_name = config.E5_MODEL_NAME

driver = GraphDatabase.driver(uri, auth=(user, password))
embedder = SentenceTransformer(embedding_model_name)


def get_llm():
    """Return an LLM instance based on configuration or environment.

    Priority: config.LLM_BACKEND -> env LLM_BACKEND -> default 'ollama'
    Supported backends: 'ollama', 'openai'
    """
    backend = config.LLM_BACKEND
    backend = backend.lower()

    if backend == "openai":
        model_name = config.OPENAI_MODEL
        api_key = config.OPENAI_API_KEY
        if not api_key:
            print("[WARN] OPENAI_API_KEY not set; OpenAI LLM may fail when invoked.")
        try:
            return ChatOpenAI(model_name=model_name, openai_api_key=api_key, temperature=0)
        except Exception as e:
            print(f"[ERROR] Failed to initialize OpenAI LLM: {e}. Falling back to Ollama.")

    # default/fallback: Ollama
    try:
        return Ollama(model=llm_model, temperature=0)
    except Exception as e:
        print(f"[ERROR] Failed to initialize Ollama LLM: {e}")
        raise


llm = get_llm()


# -------------------------------
# Test connection
# -------------------------------
def test_connection(driver):
    try:
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful!' AS message")
            print(result.single()["message"])
    except Exception as e:
        print("❌ Connection failed:", e)


# -------------------------------
# Load data
# -------------------------------
def load_data():
    """Fetch diverse data from different sources."""
    rss_articles = dataOrganizer.data_organizer.data_orginize_RSS()
    # github_repos = dataOrganizer.data_organizer.data_orginize_github()
    return rss_articles  # later, merge multiple lists if needed


# -------------------------------
# Define Ticket Schema 
# -------------------------------
class TicketSchema(BaseModel):
    ticket_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for the ticket (auto-generated if missing)"
    )
    title: str = Field(description="Short title or summary of the ticket")
    title_embedding: Optional[List[float]] = Field(
        default=None, description="Embedding vector for the title")

    type: Optional[str] = Field(default=None, description="Ticket type: data type from source")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Metadata information of the ticket such as published, author_name, and feed_title")
    description: Optional[Dict[str, str]] = Field(default=None, description="Description details of the ticket")
    source: Optional[Dict[str, str]] = Field(default=None, description="Source information of the ticket")
    tags: Optional[List[str]] = Field(default=None, description="Key word associated with the ticket")

    @field_validator("ticket_id", mode="before")
    @classmethod
    def ensure_id(cls, v):
        # If empty or None, return empty string (will be auto-generated later)
        if not v or (isinstance(v, str) and not v.strip()):
            return ""
        return v


# -------------------------------
# LangChain normalization
# -------------------------------
parser = PydanticOutputParser(pydantic_object=TicketSchema)

prompt = PromptTemplate(
    template=(
        "You are a strict data normalizer that converts any given JSON-like input "
        "into a standardized Ticket record.\n\n"
        "Output Rules:\n"
        "1. You must output ONLY a valid JSON object — no text, markdown, or explanations.\n"
        "2. Never output null, None, or empty responses. If data is missing, use null values in JSON.\n"
        "3. The JSON must always match this schema:\n"
        "{format_instructions}\n\n"
        "4. The field 'type' must be the type of the source data.\n"
        "5. If 'ticket_id' is missing, leave it blank (the system will auto-generate it).\n"
        "6. If any input field is missing, set it explicitly to null.\n"
        "7. Always ensure the result is a valid JSON object, never an array or primitive value.\n\n"
        "You need to try your best to fill in all fields, all fields will only be simple text type except metadata.\n\n"
        "Now normalize the following input into a Ticket record:\n{input_json}"
    ),
    input_variables=["input_json"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

# Replace LLMChain with RunnableSequence
normalize_chain = prompt | llm | parser


def normalize_ticket(raw_obj):
    """Normalize raw data into a TicketSchema object using the OutputParser."""
    # Pre-process: ensure ticket_id is not empty before sending to LLM
    if not raw_obj.get("ticket_id") or not str(raw_obj.get("ticket_id", "")).strip():
        raw_obj["ticket_id"] = str(uuid.uuid4())
    
    input_json = json.dumps(raw_obj, ensure_ascii=False)
    try:
        # RunnableSequence returns the parsed output directly
        result = normalize_chain.invoke({"input_json": input_json})
        
        # result is already parsed by the parser
        parsed_ticket = result

        # print("🐸 parsed ticket", parsed_ticket)

        if isinstance(parsed_ticket, TicketSchema):
            # Double-check: ensure ticket_id is never empty
            if not parsed_ticket.ticket_id or not parsed_ticket.ticket_id.strip():
                parsed_ticket.ticket_id = str(uuid.uuid4())
            print(f"✅ Normalized ticket: {parsed_ticket.ticket_id}")
            return parsed_ticket

        print(f"⚠️ Unexpected result type: {type(parsed_ticket)}")
        return None

    except Exception as e:
        print(f"⚠️ Failed to normalize record: {e}")
        return None


# -------------------------------
# Embedding with SentenceTransformer
# -------------------------------
def embed_texts(texts: List[str]):
    print("Generating embeddings...")
    clean_texts = [f"passage: {t.strip()}" for t in texts if t and t.strip()]
    start = time.time()
    embs = embedder.encode(clean_texts, normalize_embeddings=True).tolist()
    dur = time.time() - start
    print(f"✨ Embeddings generated for {len(clean_texts)} texts in {dur:.2f}s")
    return embs


# -------------------------------
# Neo4j schema and ingestion
# -------------------------------
def init_schema(dim: int):
    with driver.session() as s:
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Ticket) REQUIRE t.ticket_id IS UNIQUE")
        s.run("""
        CREATE VECTOR INDEX ticket_title_embedding IF NOT EXISTS
        FOR (t:Ticket) ON (t.title_embedding)
        OPTIONS {indexConfig: {`vector.dimensions`: $dim, `vector.similarity_function`: 'cosine'}}
        """, {"dim": dim})
    print("✅ Neo4j schema ready.")


def ingest_to_neo4j(tickets: List[TicketSchema]):
    print("🚀 Ingesting parsed Ticket entities into Neo4j...")

    query = """
    UNWIND $rows AS row

    // Root Ticket Node
    MERGE (root:Entity {ticket_id: row.ticket_id})
      SET root.title = row.title,
          root.type = coalesce(row.type, 'ticket'),
          root.title_embedding = row.title_embedding

    // Metadata Node
    WITH root, row
    FOREACH (_ IN CASE WHEN row.metadata IS NOT NULL THEN [1] ELSE [] END |
      MERGE (meta:Entity {parent_id: row.ticket_id, type:'metadata'})
        SET meta.published = row.metadata.published
      MERGE (root)-[:HAS_METADATA]->(meta)

      // Attach Type Node under Metadata
      MERGE (typeNode:Entity {parent_id: row.ticket_id, type:'type'})
        SET typeNode.name = coalesce(row.type, 'N/A')
      MERGE (meta)-[:HAS_TYPE]->(typeNode)
    )

    // Content Node (from description.summary)
    WITH root, row
    FOREACH (_ IN CASE WHEN row.description IS NOT NULL THEN [1] ELSE [] END |
      MERGE (content:Entity {parent_id: row.ticket_id, type:'content'})
        SET content.text = row.description.summary
      MERGE (root)-[:HAS_CONTENT]->(content)
    )

    // Source Node (with link + source_url)
    WITH root, row
    FOREACH (_ IN CASE WHEN row.source IS NOT NULL THEN [1] ELSE [] END |
      MERGE (source:Entity {parent_id: row.ticket_id, type:'source'})
        SET source.link = row.source.link,
            source.source_url = row.source.source_url
      MERGE (root)-[:HAS_SOURCE]->(source)
    )

    // Tag Nodes
    WITH root, row
    FOREACH (tagName IN coalesce(row.tags, []) |
      MERGE (tag:Entity {parent_id: row.ticket_id, type:'tag', name: tagName})
      MERGE (root)-[:HAS_TAG]->(tag)
    )
    """

    rows = []
    for t in tqdm(tickets, desc="Preparing tickets for Neo4j", unit="ticket"):
        rows.append({
            "ticket_id": t.ticket_id,
            "title": t.title,
            "type": t.type,
            "title_embedding": getattr(t, "title_embedding", None),

            # metadata sub-entity
            "metadata": {
                "published": t.metadata.get("published") if t.metadata else None,
            } if t.metadata else None,

            # description (for content)
            "description": {
                "summary": t.description.get("summary") if t.description else None,
            } if getattr(t, "description", None) else None,

            # source with both link and source_url
            "source": {
                "link": t.source.get("link") if t.source else None,
                "source_url": t.source.get("source_url") if t.source else None,
            } if t.source else None,

            # tags list
            "tags": t.tags if t.tags else []
        })

    # Push to Neo4j
    start = time.time()
    with driver.session() as s:
        s.run(query, {"rows": rows})
    duration = time.time() - start

    print(f"✅ Successfully ingested {len(rows)} tickets into Neo4j in {duration:.2f}s.")



# -------------------------------
# Main ingestion pipeline
# -------------------------------
def ingest_pipeline():
    raw_data = load_data()
    print(f"📦 Loaded {len(raw_data)} raw records.")

    # normalize with progress bar and timing
    normalized = []
    start_norm = time.time()
    for r in tqdm(raw_data, desc="Normalizing records", unit="rec"):
        normalized.append(normalize_ticket(r))
    normalized = [t for t in normalized if t]
    dur_norm = time.time() - start_norm
    print(f"✨ Normalization finished: {len(normalized)} valid tickets in {dur_norm:.2f}s")

    if not normalized:
        print("⚠️ No valid tickets after normalization.")
        return

    titles = [t.title for t in normalized]
    # embedding (timed inside embed_texts)
    title_embs = embed_texts(titles)

    # attach embeddings with progress
    for t, emb in tqdm(list(zip(normalized, title_embs)), desc="Attaching embeddings", unit="ticket"):
        t.title_embedding = emb

    init_schema(len(title_embs[0]))

    start_ing = time.time()
    ingest_to_neo4j(normalized)
    dur_ing = time.time() - start_ing
    print(f"Ingestion complete! Took {dur_ing:.2f}s")

    total = time.time() - start_norm
    print(f"Total pipeline time: {total:.2f}s")


if __name__ == "__main__":
    
    test_connection(driver)
    ingest_pipeline()
    
'''
    article = load_data()
    normalize_ticket(article[0])
    '''