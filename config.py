import os

from dotenv import load_dotenv

load_dotenv()

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

TEXT_MODEL = "gemini-2.5-flash"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

MAX_FILE_MB = 10
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 4
SESSION_TIMEOUT_MINUTES = 60
