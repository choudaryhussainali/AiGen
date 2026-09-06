"""All Gemini calls plus the retrieval step for notes questions."""

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, TEXT_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)


def generate(prompt):
    response = _client.models.generate_content(model=TEXT_MODEL, contents=prompt)
    text = (response.text or "").strip()
    if not text:
        raise ValueError("The model returned an empty response. Please try again.")
    return text


def generate_from_image(image_bytes, mime_type, prompt):
    part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    response = _client.models.generate_content(
        model=TEXT_MODEL, contents=[part, prompt]
    )
    text = (response.text or "").strip()
    if not text:
        raise ValueError("The model could not read that image. Please try another.")
    return text
