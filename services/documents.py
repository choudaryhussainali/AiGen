"""PDF text extraction and character window chunking."""

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


def chunk_pages(pages):
    # The page number rides along on every chunk, which is what lets the notes
    # answer cite the page a fact came from.
    step = CHUNK_SIZE - CHUNK_OVERLAP
    chunks = []
    for page in pages:
        text = page["text"]
        for start in range(0, len(text), step):
            window = text[start:start + CHUNK_SIZE].strip()
            if window:
                chunks.append({"text": window, "page": page["page"]})
            if start + CHUNK_SIZE >= len(text):
                break
    return chunks
