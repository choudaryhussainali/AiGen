"""All Gemini calls plus the retrieval step for notes questions."""

from google import genai

from config import GEMINI_API_KEY, TEXT_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)


def generate(prompt):
    response = _client.models.generate_content(model=TEXT_MODEL, contents=prompt)
    text = (response.text or "").strip()
    if not text:
        raise ValueError("The model returned an empty response. Please try again.")
    return text
