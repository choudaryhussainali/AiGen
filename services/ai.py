"""All Groq calls, local embeddings and the retrieval step for notes questions."""

import base64
import json
import time

import numpy as np
import requests
from fastembed import TextEmbedding

import config
from services import documents

# Constructed once at import. The first run downloads roughly 90 MB and caches it,
# every run after that is offline and has no request limit at all.
_embedder = TextEmbedding(model_name=config.EMBED_MODEL)


def embed_documents(texts):
    return np.array(list(_embedder.embed(texts)), dtype="float32")


def embed_query(text):
    return np.array(list(_embedder.query_embed([text]))[0], dtype="float32")


def _post(payload):
    """One POST to the OpenAI compatible endpoint Groq exposes."""
    try:
        return requests.post(
            f"{config.GROQ_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            json=payload,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
            stream=payload["stream"],
        )
    except requests.exceptions.RequestException:
        raise ValueError("Could not reach the AI service. Check your internet connection.")


def _open(messages, model, stream=False, patience=config.RATE_LIMIT_WAIT_SECONDS):
    """Starts a Groq completion, riding out rate limits where it can."""
    payload = {"model": model, "messages": messages, "temperature": 0.3, "stream": stream}
    if model.startswith("openai/gpt-oss"):
        # Hidden reasoning tokens count against the per minute token budget.
        payload["reasoning_effort"] = "low"
    if model == config.VISION_MODEL:
        payload["max_tokens"] = config.VISION_MAX_TOKENS
    response = _post(payload)
    other = {config.TEXT_MODEL: config.SUMMARY_MODEL, config.SUMMARY_MODEL: config.TEXT_MODEL}
    if response.status_code == 429 and model in other:
        # Each Groq model has its own token budget, so the other one is usually free.
        payload["model"] = other[model]
        response = _post(payload)
    wait = response.headers.get("retry-after", "")
    short = wait.isdigit() and int(wait) <= patience
    if response.status_code == 429 and short:
        # The token budget refills every second, so a short pause usually clears it.
        time.sleep(int(wait) + 0.5)
        response = _post(payload)
    if response.status_code != 200:
        raise ValueError(_status_message(response))
    return response


def _chat(messages, model, patience=config.RATE_LIMIT_WAIT_SECONDS):
    """A complete Groq reply, tidied into markdown the page can render."""
    content = _open(messages, model, patience=patience).json()["choices"][0]["message"]["content"]
    text = documents.plain_markdown(content).strip()
    if not text:
        raise ValueError("The model returned an empty response. Please try again.")
    return text


def _deltas(response):
    """Yields reply text as Groq streams it, one server sent event per line."""
    for raw in response.iter_lines():
        line = raw.decode("utf-8")
        if line.startswith("data: ") and line != "data: [DONE]":
            piece = json.loads(line[6:])["choices"][0]["delta"].get("content")
            if piece:
                yield piece


def _status_message(response):
    if response.status_code == 429 and "Request too large" in response.text:
        return "That request is bigger than the AI model accepts, so waiting will not help. Try a smaller input."
    if response.status_code == 429:
        return "The AI service is busy right now. Please wait a minute and try again."
    if response.status_code == 401:
        return "The Groq API key was rejected. Check your .env file."
    if response.status_code == 413:
        return "That input is too long for the model. Try a shorter one."
    return "The AI model returned an error. Please try again."


def generate(prompt, model=None, patience=config.RATE_LIMIT_WAIT_SECONDS):
    return _chat([{"role": "user", "content": prompt}], model or config.TEXT_MODEL, patience)


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


def _ranked_chunks(search, chunks, embeddings):
    """Indices best first, each strong match followed by its neighbours."""
    query = _normalise(np.atleast_2d(embed_query(search)))[0]
    shares = np.array(documents.keyword_shares(search, chunks), dtype="float32")
    # Keywords catch exact terms such as acronyms that the embedding blurs.
    scores = _normalise(embeddings) @ query + 0.3 * shares
    order = [int(index) for index in np.argsort(scores)[::-1]]
    picked = []
    for index in order[:config.TOP_K]:
        for near in (index, index - 1, index + 1):
            if 0 <= near < len(chunks) and near not in picked:
                picked.append(near)
    return picked + [index for index in order if index not in picked]


def _fit_budget(indices, chunks):
    """Takes indices in priority order until the context budget is spent."""
    chosen, used = [], 0
    for index in indices:
        size = len(chunks[index]["text"])
        if chosen and used + size > config.CONTEXT_CHARS:
            break
        chosen.append(index)
        used += size
    return sorted(chosen)


def _pick_chunks(question, history, chunks, embeddings):
    """Whole small documents, a named chapter, or the best matching chunks."""
    if sum(len(chunk["text"]) for chunk in chunks) <= config.CONTEXT_CHARS:
        return list(range(len(chunks)))
    search = documents.search_text(question, history)
    number = documents.section_number(question) or documents.section_number(search)
    section = documents.section_chunks(chunks, number) if number else []
    ranked = _ranked_chunks(search, chunks, embeddings)
    if section and documents.keywords(search):
        # A focused question inside a chapter reads its most relevant parts first.
        return _fit_budget([index for index in ranked if index in section], chunks)
    return _fit_budget(section or ranked, chunks)


def summarize_notes(text):
    prompt = f"""Summarise these lecture notes for a student revising them.

Notes:
{text}

Write the summary as bullet points only. Group them under "## " headings when
the notes cover more than one theme. Start every bullet with "- " and use
**bold** for the key terms. Keep each bullet to one sentence.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate(prompt, config.SUMMARY_MODEL)


def _chat_messages(system, history, question):
    messages = [{"role": "system", "content": system}]
    for turn in history:
        # Earlier answers are trimmed so the chat stays inside the token budget.
        earlier = turn["answer"][:config.HISTORY_ANSWER_CHARS]
        messages.append({"role": "user", "content": turn["question"]})
        messages.append({"role": "assistant", "content": earlier})
    messages.append({"role": "user", "content": question})
    return messages


def stream_from_notes(question, chunks, embeddings, summary, history):
    picked = _pick_chunks(question, history, chunks, embeddings)
    context = "\n\n".join(
        f"[page {chunks[index]['page']}]\n{chunks[index]['text']}" for index in picked
    )
    prompt = f"""You are a study assistant chatting with a student about a PDF they uploaded.

Summary of the whole document:
{summary}

Excerpts from the document, each marked with its page:
{context}

Answer the student fully. When they ask for more detail, an explanation of a
chapter or section, or examples, give a thorough answer built from the excerpts.
You may add general knowledge to explain an idea the document mentions, but say
when you go beyond the document. Only when neither the excerpts nor the summary
relate to the question, say the document does not cover it and name what it does
cover. After each point taken from the excerpts, cite its page as (page 3).

Format with "## " headings, "- " bullets, **bold** key terms and plain paragraphs
only. Never use tables, "###" headings or numbered headings.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    messages = _chat_messages(prompt, history, question)
    # Opening the stream here surfaces rate limit and key errors before any text is sent.
    response = _open(messages, config.TEXT_MODEL, stream=True)
    return _deltas(response), [chunks[index]["page"] for index in picked]


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


def condense_transcript(parts):
    """A short video goes in whole, a long one is condensed part by part first."""
    if len(parts) == 1:
        return parts[0]
    notes = []
    for number, part in enumerate(parts, start=1):
        prompt = f"""This is part {number} of {len(parts)} of a lecture video transcript.

Transcript part:
{part}

Write at most eight short "- " bullets of study notes for this part: the topics in
order, key ideas, definitions, examples and any steps the speaker explains. Use
**bold** for key terms and write in English.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
        notes.append(generate(prompt, config.SUMMARY_MODEL, config.VIDEO_WAIT_SECONDS))
    return "\n\n".join(notes)[:config.MAX_SUMMARY_CHARS]


def summarize_video(transcript, language):
    prompt = f"""Below is a lecture video transcript, or study notes taken from each part in order.

Transcript:
{transcript}

Explain the video in an easy to understand way for a student who has not watched
it. Use simple words and short sentences, and explain each technical term the
first time it appears. Start with "## Overview" and two or three sentences on what
the video is about. Then give a "## " heading for each main topic in the order the
video covers it, with "- " bullets that explain the idea simply and add an example
or analogy where it helps. End with "## Key Takeaways" and three to five bullets.
Use **bold** for key terms. Write the whole summary in {language}, even when the
transcript is in another language.

Do not use emojis. Do not use dash characters other than the plain hyphen."""
    return generate(prompt, config.SUMMARY_MODEL, config.VIDEO_WAIT_SECONDS)


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
