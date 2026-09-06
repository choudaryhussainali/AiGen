"""All Gemini calls plus the retrieval step for notes questions."""

import numpy as np
from google import genai
from google.genai import types

from config import EMBED_BATCH, EMBED_MODEL, GEMINI_API_KEY, TEXT_MODEL, TOP_K

_client = genai.Client(api_key=GEMINI_API_KEY)


def _raise_friendly(error):
    """Gemini quota and safety errors reach the user as readable sentences."""
    text = str(error)
    # A daily quota block lasts until midnight Pacific, a per minute one does not.
    if "PerDay" in text:
        raise ValueError("The daily Gemini free quota is used up. It resets at midnight Pacific Time.")
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        raise ValueError("The AI service is busy right now. Please wait a minute.")
    if "UNAVAILABLE" in text or "503" in text:
        raise ValueError("The AI service is under heavy load. Please try again.")
    if "API key" in text or "PERMISSION_DENIED" in text:
        raise ValueError("The Gemini API key was rejected. Check your .env file.")
    raise error


def embed(texts):
    # The embedding endpoint accepts at most 100 items per request.
    vectors = []
    for start in range(0, len(texts), EMBED_BATCH):
        try:
            response = _client.models.embed_content(
                model=EMBED_MODEL, contents=texts[start:start + EMBED_BATCH]
            )
        except Exception as error:
            _raise_friendly(error)
        vectors.extend(item.values for item in response.embeddings)
    return np.array(vectors, dtype="float32")


def generate(prompt):
    try:
        response = _client.models.generate_content(model=TEXT_MODEL, contents=prompt)
    except Exception as error:
        _raise_friendly(error)
    text = (response.text or "").strip()
    if not text:
        raise ValueError("The model returned an empty response. Please try again.")
    return text


def generate_from_image(image_bytes, mime_type, prompt):
    part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    try:
        response = _client.models.generate_content(
            model=TEXT_MODEL, contents=[part, prompt]
        )
    except Exception as error:
        _raise_friendly(error)
    text = (response.text or "").strip()
    if not text:
        raise ValueError("The model could not read that image. Please try another.")
    return text


def _normalise(matrix):
    lengths = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(lengths, 1e-10)


def _top_chunks(question, chunks, embeddings):
    """Cosine similarity is one dot product once both sides are normalised."""
    query = _normalise(embed([question]))[0]
    scores = _normalise(embeddings) @ query
    best = np.argsort(scores)[::-1][:TOP_K]
    return [chunks[index] for index in best]


def summarize_notes(text):
    prompt = f"""Summarise these lecture notes for a student revising them.

Notes:
{text}

Write the summary as bullet points only. Group them under "## " headings when
the notes cover more than one theme. Start every bullet with "- " and use
**bold** for the key terms. Keep each bullet to one sentence.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate(prompt)


def answer_from_notes(question, chunks, embeddings):
    top = _top_chunks(question, chunks, embeddings)
    context = "\n\n".join(
        f"[page {chunk['page']}]\n{chunk['text']}" for chunk in top
    )
    prompt = f"""Answer the student question using only the notes below.

Notes:
{context}

Question: {question}

Answer in two or three sentences of plain English. If the notes do not contain
the answer, reply with exactly: I could not find this in your notes

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    answer = generate(prompt)
    return answer, sorted({chunk["page"] for chunk in top})


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


def solve_paper(image_bytes, mime_type):
    prompt = """This image is from a past exam paper. Read every question in it,
then solve each one.

For each question use this exact structure:
## Question
The question exactly as written in the image.
## Solution
The full working, one step per line.
## Explanation
Two or three sentences on why the method works.

If part of the image is unreadable, say so instead of guessing.
Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate_from_image(image_bytes, mime_type, prompt)


def summarize_video(transcript):
    prompt = f"""Summarise this lecture video for a student who has not watched it.

Transcript:
{transcript}

Write a topic wise summary. Use a "## " heading for each topic the video
covers, then two or three bullets under it starting with "- ". Use **bold**
for the key terms. Keep the order the video uses.

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
