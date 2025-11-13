# TrendScout AI

A data pipeline that ingests data from RSS feeds and GitHub, normalizes it with an LLM, computes embeddings, and stores metadata in Neo4j.

## Project Structure

| File | Purpose |
|------|---------|
| `metadataToNeo4j.py` | Main pipeline: data loading, LLM normalization, embedding computation, Neo4j ingestion |
| `dataOrganizer.py` | Helper to coordinate data ingestion |
| `Data_Scraping/data_RSS.py` | RSS feed ingestion |
| `Data_Scraping/data_github.py` | GitHub API data collection |
| `config.py` | Configuration (use environment variables for secrets) |

## Neo4j Database Setup
Go to [Neo4j Aura](https://neo4j.com/product/auradb/) and create an instance. Copy the password and database URL (found in the instance dropdown at top left).

### Database Schema
The pipeline creates the following node structure:

```
Ticket (Root Entity)
├── HAS_METADATA → Metadata
│   └── HAS_TYPE → Type
├── HAS_CONTENT → Content
├── HAS_SOURCE → Source
└── HAS_TAG → Tag (multiple)
```

**Ticket Node:**
- `ticket_id` (UNIQUE, auto-generated)
- `title` (indexed with vector embedding)
- `type` (data type from source)
- `title_embedding` (cosine similarity vector index)

**Child Nodes (Entity type):**
- **Metadata**: published date
- **Type**: source data type
- **Content**: summary/description text
- **Source**: link, source_url
- **Tags**: keywords (multiple tags per ticket) 

## Embedding Model E5
Please login Huggingface account to use embedding model E5 with commend

`
huggingface-cli login
`

## Quick Start

### 1. Setup Environment
```powershell
conda create -n "transcoutAI" python=3.9
conda activate transcoutAI
pip install -r requirements.txt
```

### 2. Configure Credentials
Set environment variables or update `config.py`:
```
GITHUB_TOKEN
NEO4J_URI
NEO4J_USER
NEO4J_PASSWORD
OPENAI_API_KEY 
OPENAI_MODEL (Recommend to use OPENAI rather then Ollama)
E5_MODEL_NAME (E% from huggingface)
```

### 3. Run Pipeline
```powershell
python metadataToNeo4j.py
```

## Dependencies
- neo4j >= 5.0.0
- sentence-transformers >= 2.2.2
- openai >= 1.0.0
- requests >= 2.28.0
- feedparser >= 6.0.0
- torch >= 2.0.0
- transformers >= 4.30.0

**Note:** For GPU support with PyTorch, install via https://pytorch.org

