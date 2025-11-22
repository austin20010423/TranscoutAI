GITHUB_TOKEN = "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"
SEARCH_QUERY = "topic:generative-ai topic:llm language:python"
SORT_BY = "stars"
ORDER = "desc"


# --- NEO4j CONFIG ---
NEO4J_URI = "neo4j+s://f50e7d64.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neHNXTZrPki9-HAuOKKknRXoP49Wsoweg0c-Yy86i-I"


# --- OPENAI  AND EMBEDDING MODEL CONFIG ---
OPEN_MODEL = "gemma3:270m"
E5_MODEL_NAME = "intfloat/e5-base-v2"
OPENAI_API_KEY = "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"

# LLM backend selection: 'ollama' (default) or 'openai'.
# You can override via environment variable LLM_BACKEND or set here.
LLM_BACKEND = "openai"  # options: 'ollama' or 'openai'

# If using OpenAI as backend, specify the model name (can also be set via OPENAI_MODEL env var)
OPENAI_MODEL = "gpt-4o"
