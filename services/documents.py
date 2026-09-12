"""PDF text extraction and paragraph aware chunking."""

import re

from pypdf import PdfReader

from config import CHUNK_OVERLAP, CHUNK_SIZE


def extract_pdf_pages(file_stream):
    reader = PdfReader(file_stream)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({"page": number, "text": text})
    if not pages:
        raise ValueError("No readable text found in that PDF.")
    return pages


def _split_long(paragraph):
    """A paragraph over the cap is broken at sentence ends, never mid word."""
    parts, buffer = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
        if buffer and len(buffer) + len(sentence) + 1 > CHUNK_SIZE:
            parts.append(buffer)
            buffer = sentence
        else:
            buffer = (buffer + " " + sentence).strip()
    if buffer:
        parts.append(buffer)
    return parts


def _split_units(text):
    units = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= CHUNK_SIZE:
            units.append(paragraph)
        else:
            units.extend(_split_long(paragraph))
    return units


def _pack(units, page):
    """Greedily fill windows, carrying about CHUNK_OVERLAP characters forward."""
    chunks, buffer = [], ""
    for unit in units:
        if buffer and len(buffer) + len(unit) + 2 > CHUNK_SIZE:
            chunks.append({"text": buffer, "page": page})
            # The raw slice usually lands inside a word, so drop that fragment.
            carried = buffer[-CHUNK_OVERLAP:].split(None, 1)
            buffer = carried[1] if len(carried) == 2 else ""
        buffer = (buffer + "\n\n" + unit).strip() if buffer else unit
    if buffer:
        chunks.append({"text": buffer, "page": page})
    return chunks


def chunk_pages(pages):
    # The page number still rides on every chunk, which is what keeps the
    # citations in the notes answer exact.
    chunks = []
    for page in pages:
        chunks.extend(_pack(_split_units(page["text"]), page["page"]))
    return chunks
