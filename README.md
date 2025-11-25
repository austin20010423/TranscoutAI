# TrendScout AI

**Conversational Market Intelligence for AI Startups**

TrendScout AI is a comprehensive system that aggregates market data, stores it in a Neo4j knowledge graph, and provides an interactive, Gemini-like chat interface for querying the data using RAG (Retrieval-Augmented Generation).

## Project Structure

| File | Purpose |
|------|---------|
| `app.py` | **[NEW]** Streamlit web application (Gemini clone UI) for interactive chat. |
| `llm_response.py` | **[NEW]** RAG backend: retrieves data and generates LLM responses. |
| `retriever.py` | **[NEW]** Semantic search logic using E5 embeddings and Neo4j. |
| `metadataToNeo4j.py` | Main pipeline: data loading, LLM normalization, embedding computation, Neo4j ingestion. |
| `dataOrganizer.py` | Helper to coordinate data ingestion. |
| `config.py` | Configuration (API keys, database URI, model settings). |
| `Data_Scraping/` | Custom Data Scraping modules. |

## Features

-   **Interactive Chat Interface**: A sleek, dark-mode web app built with Streamlit that mimics the Google Gemini experience.
-   **RAG (Retrieval-Augmented Generation)**: Answers user queries by retrieving relevant "tickets" (market data) from Neo4j and synthesizing a response using OpenAI's GPT-4o.
-   **Semantic Search**: Uses E5 embeddings to find relevant data based on meaning, not just keywords.
-   **Knowledge Graph**: Stores structured data (startups, technologies, trends) in Neo4j for rich relationship querying.

## Component Details

### `llm_response.py`
This module handles the generation of natural language responses using RAG (Retrieval-Augmented Generation).
-   **Function**: `generate_response(user_query)`
-   **Process**:
    1.  **Retrieve**: Calls `retriever.text_query_to_results` to fetch relevant tickets from Neo4j.
    2.  **Contextualize**: Formats the retrieved JSON data into a context string.
    3.  **Generate**: Sends the user query and context to OpenAI's GPT-4o with a system prompt designed for a tech knowledge assistant.
    4.  **Return**: Returns a dictionary with the generated `answer` and the source `sources`.

### `retriever.py`
This module implements the semantic search and retrieval logic.
-   **Key Functions**:
    -   `extract_entities_with_gpt4(user_query)`: Uses GPT-4o-mini to parse the user's natural language query into structured filters (tags, locations, sources) and a search summary.
    -   `embed_e5_query(text)`: Generates a vector embedding for the search summary using the E5 model.
    -   `semantic_search_with_tag_filter_in_neo4j(...)`: Executes a hybrid search in Neo4j:
        -   **Filtered Exact Search (KNN)**: Tries to match specific tags, locations, or sources first.
        -   **Vector Index (ANN)**: Falls back to pure semantic vector search if no exact matches are found.
    -   `text_query_to_results(user_query)`: The main entry point that orchestrates the extraction, embedding, and search steps to return ranked results.

## Quick Start

### 1. Setup Environment

```bash
conda create -n "transcoutAI" python=3.9
conda activate transcoutAI
pip install -r requirements.txt
```

### 2. Configure Credentials

Update `config.py` with your credentials. **Do not commit real keys to version control.**

```python
# config.py
GITHUB_TOKEN = "your_github_token"
NEO4J_URI = "neo4j+s://your-db-instance.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_neo4j_password"
OPENAI_API_KEY = "your_openai_api_key"

# Models
E5_MODEL_NAME = "intfloat/e5-base-v2"
OPENAI_MODEL = "gpt-4o"
```

### 3. Build the Database (Data Pipeline)

If you haven't ingested data yet, run the pipeline:

```bash
# Login to Hugging Face for E5 model access if needed
huggingface-cli login

# Run the ingestion script
python metadataToNeo4j.py
```

### 4. Run the Application

Launch the Streamlit chat interface:

```bash
streamlit run app.py
```

The app will open in your browser (usually at `http://localhost:8501`).

## Neo4j Database Schema

The pipeline creates the following node structure:

```
Ticket (Root Entity)
├── HAS_METADATA → Metadata
│   └── HAS_TYPE → Type
├── HAS_CONTENT → Content
├── HAS_SOURCE → Source
└── HAS_TAG → Tag (multiple)
```

-   **Ticket Node**: `ticket_id`, `title`, `type`, `title_embedding`
-   **Child Nodes**: `Metadata` (date), `Type` (source type), `Content` (summary), `Source` (url), `Tags` (keywords)

## Dependencies

-   `streamlit >= 1.50.0`
-   `neo4j >= 5.0.0`
-   `sentence-transformers >= 2.2.2`
-   `openai >= 1.0.0`
-   `requests >= 2.28.0`
-   `feedparser >= 6.0.0`
-   `torch >= 2.0.0`
-   `transformers >= 4.30.0`

**Note:** For GPU support with PyTorch, install via [pytorch.org](https://pytorch.org).
