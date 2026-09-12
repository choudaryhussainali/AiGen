import os

from dotenv import load_dotenv

load_dotenv()

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
REQUEST_TIMEOUT_SECONDS = 120

TEXT_MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "qwen/qwen3.8-27b"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

MAX_FILE_MB = 10
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 4
SESSION_TIMEOUT_MINUTES = 60

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Add it to .env before starting the server.")
