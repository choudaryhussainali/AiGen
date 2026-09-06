"""All Gemini calls plus the retrieval step for notes questions."""

import numpy as np
from google import genai
from google.genai import types

from config import EMBED_MODEL, GEMINI_API_KEY, TEXT_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)


def embed(texts):
    response = _client.models.embed_content(model=EMBED_MODEL, contents=texts)
    vectors = [item.values for item in response.embeddings]
    return np.array(vectors, dtype="float32")


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


def summarize_notes(text):
    prompt = f"""Summarise these lecture notes for a student revising them.

Notes:
{text}

Write the summary as bullet points only. Group them under "## " headings when
the notes cover more than one theme. Start every bullet with "- " and use
**bold** for the key terms. Keep each bullet to one sentence.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate(prompt)


def build_exam_plan(outline):
    prompt = f"""You are helping a university student prepare for an exam.

Course outline:
{outline}

Break the outline into its topics. For every topic write:
## Topic name
A short paragraph explaining what the topic covers.
- **Focus on:** the parts most likely to be examined
- **Common mistakes:** what students usually get wrong

Cover every topic in the outline and add nothing that is not in it.
Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate(prompt)


def explain_topic(topic):
    prompt = f"""Explain the topic below to a university student in simple English.

Topic: {topic}

Use this exact structure and nothing else:
## Definition
One short paragraph in plain language.
## Real World Analogy
One short paragraph comparing it to something familiar.
## Key Points
Exactly three bullets, each starting with "- " and using **bold** for the
important term.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate(prompt)
