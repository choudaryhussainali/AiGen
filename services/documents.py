"""PDF text extraction, chunking, passage matching and answer text helpers."""

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
    # Keeping the captured gaps preserves line breaks, so headings stay on their own line.
    pieces = re.split(r"(?<=[.!?])(\s+)", paragraph)
    for sentence, gap in zip(pieces[::2], pieces[1::2] + [""]):
        if buffer.strip() and len(buffer) + len(sentence) > CHUNK_SIZE:
            parts.append(buffer.strip())
            buffer = ""
        buffer += sentence + gap
    if buffer.strip():
        parts.append(buffer.strip())
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


_STOPWORDS = {
    "about", "and", "are", "can", "chap", "chapter", "chp", "detail", "details",
    "does", "explain", "for", "from", "how", "lecture", "lesson", "module", "more",
    "notes", "part", "please", "section", "tell", "that", "the", "this", "unit",
    "week", "what", "when", "where", "which", "why", "with", "you",
}


def keywords(text):
    """Distinct content words, the part of a question worth matching exactly."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in _STOPWORDS}


_SECTION = (
    r"(?:chapter|chap|chp|ch|unit|lecture|lesson|module|part|week)"
    r"(?:\.?\s*([0-9]+)|[.\s]+([ivx]+|one|two|three|four|five|six|seven|eight|nine|ten))\b"
)
_NUMBERS = dict(zip("one two three four five six seven eight nine ten".split(), range(1, 11)))
_NUMBERS.update(zip("i ii iii iv v vi vii viii ix x".split(), range(1, 11)))


def _to_number(digits, name):
    return int(digits) if digits else _NUMBERS.get(name.lower())


def section_number(text):
    """The chapter, unit or lecture number a question names, if it names one."""
    match = re.search(r"\b" + _SECTION, text, re.IGNORECASE)
    return _to_number(*match.groups()) if match else None


def section_chunks(chunks, number):
    """Every chunk from the heading that names the section to the next heading."""
    heading = re.compile(r"^\s*" + _SECTION, re.IGNORECASE | re.MULTILINE)
    picked, current = [], None
    for index, chunk in enumerate(chunks):
        found = [n for n in (_to_number(*g) for g in heading.findall(chunk["text"])) if n]
        if current == number or number in found:
            picked.append(index)
        if found:
            current = found[-1]
    return picked


def plain_markdown(text):
    """Rewrites tables and deep headings into the four forms the page renders."""
    # The project uses plain hyphens only, but models still emit typographic dashes.
    text = text.replace(chr(0x2014), "-").replace(chr(0x2013), "-").replace(chr(0x2011), "-")
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and re.fullmatch(r"[\s:|-]+", stripped):
            continue
        if stripped.startswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            line = "- " + "; ".join(cell for cell in cells if cell)
        elif stripped.startswith("#"):
            line = "## " + stripped.lstrip("#").strip()
        lines.append(line)
    return "\n".join(lines)


def cited_pages(answer, shown):
    """Pages the answer names, limited to the pages it was actually shown."""
    groups = re.findall(r"pages?\s+([\d\s,&and]+)", answer, re.IGNORECASE)
    named = {int(number) for group in groups for number in re.findall(r"\d+", group)}
    return sorted(named & set(shown))
