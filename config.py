GITHUB_TOKEN = "github token"
SEARCH_QUERY = "topic:generative-ai topic:llm language:python"
SORT_BY = "stars"
ORDER = "desc"


# --- NEO4j CONFIG ---
NEO4J_URI = "neo4j+s://f50e7d64.databases.neo4j"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


# --- OPENAI  AND EMBEDDING MODEL CONFIG ---
OPEN_MODEL = "gemma3:270m"
E5_MODEL_NAME = "intfloat/e5-base-v2"
OPENAI_API_KEY = "api key"

# LLM backend selection: 'ollama' (default) or 'openai'.
# You can override via environment variable LLM_BACKEND or set here.
LLM_BACKEND = "openai"  # options: 'ollama' or 'openai'

# If using OpenAI as backend, specify the model name (can also be set via OPENAI_MODEL env var)
OPENAI_MODEL = "gpt-4o"
