"""All Groq calls, local embeddings and the retrieval step for notes questions."""

import base64

import numpy as np
import requests
from fastembed import TextEmbedding

import config

# Constructed once at import. The first run downloads roughly 90 MB and caches it,
# every run after that is offline and has no request limit at all.
_embedder = TextEmbedding(model_name=config.EMBED_MODEL)


def embed_documents(texts):
    return np.array(list(_embedder.embed(texts)), dtype="float32")


def embed_query(text):
    return np.array(list(_embedder.query_embed([text]))[0], dtype="float32")


def _chat(messages, model):
    """One POST to the OpenAI compatible endpoint Groq exposes."""
    payload = {"model": model, "messages": messages, "temperature": 0.3}
    if model.startswith("openai/gpt-oss"):
        # Hidden reasoning tokens count against the per minute token budget.
        payload["reasoning_effort"] = "low"
    try:
        response = requests.post(
            f"{config.GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json=payload,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException:
        raise ValueError("Could not reach the AI service. Check your internet connection.")
    if response.status_code != 200:
        raise ValueError(_status_message(response.status_code))
    text = response.json()["choices"][0]["message"]["content"].strip()
    if not text:
        raise ValueError("The model returned an empty response. Please try again.")
    return text


def _status_message(status):
    if status == 429:
        return "The AI service is busy right now. Please wait a minute and try again."
    if status == 401:
        return "The Groq API key was rejected. Check your .env file."
    if status == 413:
        return "That input is too long for the model. Try a shorter one."
    return "The AI model returned an error. Please try again."


def generate(prompt, model=None):
    return _chat([{"role": "user", "content": prompt}], model or config.TEXT_MODEL)


def generate_from_image(image_bytes, mime_type, prompt):
    encoded = base64.b64encode(image_bytes).decode("ascii")
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
    ]
    return _chat([{"role": "user", "content": content}], config.VISION_MODEL)


def _normalise(matrix):
    lengths = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(lengths, 1e-10)


def _top_chunks(question, chunks, embeddings):
    """Cosine similarity is one dot product once both sides are normalised."""
    query = _normalise(np.atleast_2d(embed_query(question)))[0]
    scores = _normalise(embeddings) @ query
    best = np.argsort(scores)[::-1][:config.TOP_K]
    return [chunks[index] for index in best]


def summarize_notes(text):
    prompt = f"""Summarise these lecture notes for a student revising them.

Notes:
{text}

Write the summary as bullet points only. Group them under "## " headings when
the notes cover more than one theme. Start every bullet with "- " and use
**bold** for the key terms. Keep each bullet to one sentence.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate(prompt, config.SUMMARY_MODEL)


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
    return generate(prompt, config.SUMMARY_MODEL)


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
    return generate(prompt, config.SUMMARY_MODEL)


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
