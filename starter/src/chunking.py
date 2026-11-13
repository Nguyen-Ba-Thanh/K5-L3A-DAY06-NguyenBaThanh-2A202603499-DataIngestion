"""Page-bounded chunks with stable IDs and exact normalized offsets."""
import hashlib
import re
from .models import Chunk, DocumentPage


def make_chunk(page, start, end, method):
    text = page.text[start:end]
    key = f"{page.document_id}:{page.page}:{method}:{start}:{end}:{text}"
    return Chunk(hashlib.sha256(key.encode()).hexdigest(), page.document_id, page.source, page.page,
                 text, {**page.metadata, "start": start, "end": end})


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    chunks = []
    for start in range(0, len(page.text), size - overlap):
        end = min(start + size, len(page.text))
        chunks.append(make_chunk(page, start, end, f"fixed-{size}-{overlap}"))
        if end == len(page.text):
            break
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    if max_size <= 0:
        raise ValueError("max_size must be positive")
    chunks, start, end = [], None, None
    for match in re.finditer(r"[^\n]+", page.text):
        pos, stop = match.span()
        while pos < stop:
            cut = min(pos + max_size, stop)
            if cut < stop:
                boundaries = [m.end() + pos for m in re.finditer(r"\s+", page.text[pos:cut])]
                if boundaries:
                    cut = boundaries[-1]
            if start is not None and cut - start > max_size:
                chunks.append(make_chunk(page, start, end, f"paragraph-{max_size}"))
                start = None
            if start is None:
                start = pos
            end = cut
            pos = cut
    if start is not None:
        chunks.append(make_chunk(page, start, end, f"paragraph-{max_size}"))
    return chunks
