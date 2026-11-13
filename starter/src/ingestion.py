"""Normalize and load documents without losing source positions."""
import json
import logging
import re
import unicodedata
from pathlib import Path
from .models import DocumentPage


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    return "\n\n".join(re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip())


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    from pypdf import PdfReader
    pages = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        try:
            text = normalize_text(page.extract_text() or "")
        except Exception:
            logging.exception("Extraction failed: %s page %s", path.name, number)
            continue
        if not text:
            logging.warning("Empty page; OCR not performed: %s page %s", path.name, number)
            continue
        pages.append(DocumentPage(document_id, source, number, text))
    return pages


def load_jsonl(path: Path) -> list[DocumentPage]:
    pages = [DocumentPage(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len({(p.document_id, p.page) for p in pages}) != len(pages):
        raise ValueError("Duplicate source page IDs")
    for page in pages:
        if not page.source or not page.text or normalize_text(page.text) != page.text:
            raise ValueError("Empty source/text or unnormalized corpus")
    return pages
