"""All Gemini calls plus the retrieval step for notes questions."""

from google import genai

from config import GEMINI_API_KEY

_client = genai.Client(api_key=GEMINI_API_KEY)
