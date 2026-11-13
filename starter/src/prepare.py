"""Build reproducible source units and freeze an evidence-verified benchmark.

Run BEFORE retrieval. Text comes only from the downloaded original, never generated.
"""
import argparse
import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from .ingestion import normalize_text
from .models import DocumentPage

ROOT = Path(__file__).resolve().parents[2]
URL = "https://www.gutenberg.org/ebooks/11.txt.utf-8"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


# Authored before running retrieval. Dev chapters I-IX; test chapters X-XII.
# needle selects a verbatim paragraph, not a generated quote or retrieval result.
QUESTIONS = [
 (1, "What was in the jar Alice picked up while falling?", "it was labelled", "The orange-marmalade jar was empty.", None),
 (1, "Before drinking from the labelled bottle, what did Alice check?", "see whether it’s marked", "She checked whether it was marked poison.", 1),
 (1, "How were the words on the little cake written?", "beautifully marked in currants", "EAT ME was marked in currants.", None),
 (2, "What caused Alice to shrink while she was talking about her identity?", "the cause of this was the fan", "She was holding the Rabbit’s fan and dropped it to avoid shrinking away.", 2),
 (2, "Which two languages did Alice think the Mouse might speak?", "Perhaps it doesn’t understand English", "English and French.", None),
 (3, "What did Alice distribute as prizes after the race?", "pulled out a box of comfits", "A box of comfits, one each.", None),
 (3, "What prize did the Dodo give to Alice herself?", "presented the thimble", "A thimble.", 3),
 (4, "What did the White Rabbit ask Alice to fetch from the house?", "fetch me a pair of gloves", "A pair of gloves and a fan.", None),
 (4, "What happened to the little pebbles thrown into the room?", "turning into little cakes", "They turned into little cakes on the floor.", None),
 (5, "What did the Caterpillar say the two sides would do to Alice?", "One side will make you grow taller", "One side makes her taller and the other shorter.", 5),
 (5, "Why did the Pigeon refuse to believe Alice was a little girl?", "never _one_ with such a neck", "The Pigeon had never seen a little girl with such a neck.", None),
 (6, "Why was Alice sneezing in the Duchess’s kitchen?", "too much pepper in that soup", "There was too much pepper in the soup.", None),
 (7, "What substance did the Hatter say would not suit the watch’s works?", "butter wouldn’t suit", "Butter.", 7),
 (8, "What living creatures served as the balls and mallets at croquet?", "the balls were live", "Live hedgehogs were balls and live flamingoes were mallets.", None),
 (9, "Why did the Mock Turtle’s class call their teacher Tortoise?", "because he taught us", "Because he taught them (a pun on taught us).", None),
 (10, "In the song, what creature was treading on the whiting’s tail?", "treading on my tail", "A porpoise.", 10),
 (10, "Why does the Mock Turtle say a fish needs a porpoise?", "no wise fish would go anywhere", "No wise fish would go anywhere without a porpoise, a pun on purpose.", None),
 (11, "What did the first witness bring into court?", "The first witness was the Hatter", "A teacup and a piece of bread-and-butter.", 11),
 (11, "How did court officers suppress the cheering guinea-pig?", "a large canvas bag", "They put it head first into a canvas bag and sat on it.", None),
 (12, "What did Alice call the court just before the cards flew at her?", "You’re nothing but a pack of cards", "A pack of cards.", 12),
]


def prepare(download=False):
    if (ROOT / "benchmark/freeze.json").exists():
        raise RuntimeError("Benchmark already frozen. Do not silently rewrite an evaluated test set.")
    raw_path = ROOT / "data/raw/alice.txt"
    if download:
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(urlopen(URL, timeout=60).read())
    raw = raw_path.read_text(encoding="utf-8-sig")
    body = raw.split("*** START OF THE PROJECT GUTENBERG EBOOK", 1)[1]
    body = body.split("*** END OF THE PROJECT GUTENBERG EBOOK", 1)[0]
    matches = list(re.finditer(r"(?m)^CHAPTER ([IVX]+)\.\s*\n([^\n]+)", body))
    if len(matches) != 12:
        raise ValueError("Expected twelve chapter headings; source format changed")
    pages, records = [], []
    for chapter, match in enumerate(matches, 1):
        stop = matches[chapter].start() if chapter < len(matches) else len(body)
        text = normalize_text(body[match.end():stop])
        # Source-unit boundaries use whole paragraphs, >=1,500 normalized chars.
        units, pos, start = [], 0, 0
        for paragraph in text.split("\n\n"):
            pos += len(paragraph)
            if pos - start >= 1800:
                units.append((start, pos))
                start = pos + 2
            pos += 2
        if start < len(text):
            if units:
                units[-1] = (units[-1][0], len(text))
            else:
                units.append((0, len(text)))
        for start, end in units:
            page_id = len(pages) + 1
            content = text[start:end]
            if len(content) < 1500:
                raise ValueError("Insufficient source-unit length")
            metadata = {"chapter": chapter, "chapter_title": match.group(2).strip(), "language": "en",
                        "chapter_start": start, "chapter_end": end}
            page = DocumentPage("alice-11", URL, page_id, content, metadata)
            pages.append(page)
            records.append({"page": page_id, "chapter": chapter, "start": start, "end": end,
                            "characters": len(content), "sha256": hashlib.sha256(content.encode()).hexdigest()})
    questions = []
    for index, (chapter, question, needle, answer, filter_chapter) in enumerate(QUESTIONS, 1):
        candidates = [(p, para) for p in pages if p.metadata["chapter"] == chapter
                      for para in p.text.split("\n\n") if needle in para]
        if len(candidates) != 1:
            raise ValueError(f"Evidence ambiguous/missing for q{index:02}: {needle!r} ({len(candidates)})")
        page, quote = candidates[0]
        questions.append({"id": f"q{index:02}", "split": "dev" if index <= 15 else "test",
            "question": (f"In Chapter {filter_chapter}, " + question[0].lower() + question[1:]) if filter_chapter else question,
            "expected_answer": answer, "gold_source_id": page.document_id, "gold_page": page.page,
            "evidence_quote": quote, "filter": {"chapter": filter_chapter} if filter_chapter else {},
            "type": "metadata" if filter_chapter else "paraphrase"})
    write_jsonl(ROOT / "data/pages.jsonl", [asdict(p) for p in pages])
    write_jsonl(ROOT / "benchmark/questions.jsonl", questions)
    now = datetime.now(timezone.utc).isoformat()
    write_json(ROOT / "data/manifest.json", {"source_id": "alice-11", "title": "Alice’s Adventures in Wonderland",
        "author": "Lewis Carroll (1832–1898)", "source_path_or_url": URL, "local_path": "data/raw/alice.txt",
        "license_or_permission": "Public domain literary text; Project Gutenberg redistribution terms retained in original file. Author died 1898. No modern illustrations included.",
        "license_url": "https://www.gutenberg.org/policy/license.html", "catalog_url": "https://www.gutenberg.org/ebooks/11",
        "accessed_at": now, "snapshot": "Gutenberg edition last updated 2025-06-26; exact bytes hashed below",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(), "physical_pages": None,
        "counting_rule": "Chapter text only, front matter/TOC/license excluded from retrieval. Sequential whole-paragraph units targeting 1800 chars, final remainder merged within chapter; every unit >=1500 NFC normalized chars. page is synthetic source-unit ID, NOT a printed page.",
        "content_units": len(pages), "units": records})
    write_json(ROOT / "benchmark/freeze.json", {"frozen_at": now, "questions_sha256": hashlib.sha256((ROOT / "benchmark/questions.jsonl").read_bytes()).hexdigest(),
        "corpus_sha256": hashlib.sha256((ROOT / "data/pages.jsonl").read_bytes()).hexdigest(),
        "config_sha256": hashlib.sha256((ROOT / "configs/strategies.json").read_bytes()).hexdigest(),
        "split_rule": "q01-q15: chapters I-IX dev; q16-q20: chapters X-XII test. Same book/characters cause residual topic leakage.",
        "selection": json.loads((ROOT / "configs/strategies.json").read_text())["selection"],
        "evidence_review": "Verbatim paragraphs verified by prepare script; question/answer drafted by Codex. Student human review pending.",
        "coherence_sampling": "First 10 source-unit IDs, offset equal to half the text length; all chunks covering anchor. Chosen before retrieval."})
    print(f"Prepared {len(pages)} source units; {len(questions)} questions (15 dev / 5 test)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    prepare(parser.parse_args().download)
