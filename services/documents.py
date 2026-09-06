"""PDF text extraction and character window chunking."""

from pypdf import PdfReader


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
