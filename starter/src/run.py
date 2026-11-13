"""Reproducible ingestion, dev selection, then held-out test evaluation."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import logging
import os
import platform
import statistics
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, evidence_key, golds, summarize
from .ingestion import load_jsonl
from .prepare import ROOT, write_json, write_jsonl
from .store import QdrantStore, ALLOWED_FILTERS


def read_questions():
    return [json.loads(line) for line in (ROOT / "benchmark/questions.jsonl").read_text(encoding="utf-8").splitlines()]


def validate(pages, questions):
    freeze = json.loads((ROOT / "benchmark/freeze.json").read_text(encoding="utf-8"))
    for path, key in [("data/pages.jsonl", "corpus_sha256"), ("benchmark/questions.jsonl", "questions_sha256"), ("configs/strategies.json", "config_sha256")]:
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != freeze[key]:
            raise ValueError(f"Frozen input changed: {path}. Disclose changes; create a new benchmark version.")
    if len(pages) < 30 or any(len(p.text) < 1500 for p in pages):
        raise ValueError("Need >=30 normalized source units of >=1500 characters")
    lookup = {(p.document_id, p.page): p for p in pages}
    if len({q["id"] for q in questions}) != len(questions):
        raise ValueError("Duplicate question IDs")
    if any(q["split"] not in {"dev", "test"} for q in questions):
        raise ValueError("Invalid split")
    if sum(q["split"] == "dev" for q in questions) < 15 or sum(q["split"] == "test" for q in questions) < 5:
        raise ValueError("Need >=15 dev and >=5 test")
    if sum(bool(q.get("filter")) for q in questions) < 3 or not any(q.get("filter") and q["split"] == "test" for q in questions):
        raise ValueError("Insufficient filter questions")
    for q in questions:
        if not q["question"].strip() or not q["expected_answer"].strip():
            raise ValueError("Missing question or answer")
        for gold in golds(q):
            page = lookup[(gold["source_id"], gold["page"])]
            if not gold["evidence_quote"].strip() or evidence_key(gold["evidence_quote"]) not in evidence_key(page.text):
                raise ValueError(f"Missing evidence: {q['id']}")
        filters = q.get("filter", {})
        if set(filters) - ALLOWED_FILTERS:
            raise ValueError("Invalid filter field")
        if filters and not any(all(p.metadata.get(k) == v for k, v in filters.items()) for p in pages):
            raise ValueError("Filter matches no source")
    return freeze


def write_csv(path, rows, fields=None):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def audit_samples(out, pages, chunks_by_strategy, traces):
    coherence, grounding, metadata = [], [], []
    lookup = {(p.document_id, p.page): p for p in pages}
    for strategy, chunks in chunks_by_strategy.items():
        for page in sorted(pages, key=lambda p: (p.document_id, p.page))[:10]:
            anchor = len(page.text) // 2
            for chunk in chunks:
                if chunk.document_id == page.document_id and chunk.page == page.page and chunk.metadata["start"] <= anchor < chunk.metadata["end"]:
                    coherence.append({"strategy": strategy, "page": page.page, "anchor": anchor, "chunk_id": chunk.chunk_id,
                        "text": chunk.text, "score_0_2": "", "reason": "", "reviewer": "", "status": "pending_human"})
    for trace in traces:
        if trace["split"] != "test":
            continue
        grounding.append({"strategy": trace["strategy"], "question_id": trace["id"], "question": trace["question"],
            "gold_evidence": trace["evidence_quote"], "top3_text": "\n---\n".join(h["text"] for h in trace["hits"]),
            "score_0_2": "", "reason": "", "reviewer": "", "status": "pending_human"})
        for rank, hit in enumerate(trace["hits"], 1):
            m = hit["metadata"]
            page = lookup.get((m.get("document_id"), m.get("page")))
            check = bool(page and m.get("source") == page.source and all(m.get(k) == page.metadata.get(k) for k in ("chapter", "language"))
                         and page.text[m.get("start", 0):m.get("end", 0)] == hit["text"])
            metadata.append({"strategy": trace["strategy"], "question_id": trace["id"], "rank": rank, "chunk_id": hit["chunk_id"],
                "metadata": json.dumps(m, ensure_ascii=False), "automatic_source_match": check,
                "human_correct": "", "reason": "", "reviewer": "", "status": "pending_human"})
    write_csv(out / "audit_coherence.csv", coherence)
    write_csv(out / "audit_grounding.csv", grounding)
    write_csv(out / "audit_metadata.csv", metadata)
    # Automated checks are explicitly separate from human audit.
    checks = []
    for strategy in "ABC":
        rows = [m for m in metadata if m["strategy"] == strategy]
        for split in ("dev", "test"):
            filtered = [t for t in traces if t["strategy"] == strategy and t["split"] == split and t.get("filter")]
            compliant = sum(all(all(h["metadata"].get(k) == v for k, v in t["filter"].items()) for h in t["hits"]) and len(t["hits"]) == 3 for t in filtered)
            checks.append({"strategy": strategy, "split": split, "source_matches": sum(r["automatic_source_match"] for r in rows),
                          "records_checked_test_only": len(rows), "filter_compliant": compliant, "filter_questions": len(filtered)})
    write_json(out / "automated_metadata_checks.json", checks)


def run(args, out):
    pages, questions = load_jsonl(ROOT / "data/pages.jsonl"), read_questions()
    freeze = validate(pages, questions)
    config = json.loads((ROOT / "configs/strategies.json").read_text())
    write_json(out / "input_freeze.json", freeze)
    if args.validate_only:
        write_json(out / "validation.json", {"valid": True, "source_units": len(pages), "questions": len(questions)})
        print(f"Validated {len(pages)} source units and {len(questions)} questions")
        return
    os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    # Windows hosts may not permit symlinks; official hub fallback is regular files.
    import huggingface_hub.file_download as hub_download
    hub_download.are_symlinks_supported = lambda *a, **k: False
    from huggingface_hub import snapshot_download
    started = time.perf_counter()
    local = snapshot_download(config["model"], revision=config["revision"],
        allow_patterns=["*.json", "*.safetensors", "*.txt"], cache_dir=str(ROOT / ".cache/huggingface/hub"), local_files_only=args.offline)
    embedder = MyEmbedder(local)
    load_seconds = time.perf_counter() - started
    store = QdrantStore(ROOT / ".qdrant", embedder.dimensions)
    chunks_by_strategy, resources = {}, []
    try:
        b_chunks = [c for p in pages for c in by_paragraph(p, config["B"]["size"])]
        b_vectors = None
        for strategy in "ABC":
            start = time.perf_counter()
            chunks = [c for p in pages for c in fixed_size(p, config["A"]["size"], config["A"]["overlap"])] if strategy == "A" else b_chunks
            chunks_by_strategy[strategy] = chunks
            token_lengths = [len(embedder.model.tokenizer.encode(c.text, truncation=False)) for c in chunks]
            vector_start = time.perf_counter()
            vectors = b_vectors if strategy == "C" else embedder.embed_documents([c.text for c in chunks])
            vector_seconds = time.perf_counter() - vector_start
            if strategy == "B":
                b_vectors = vectors
            store_start = time.perf_counter()
            store.upsert(strategy, chunks, vectors)
            before = store.count(strategy)
            store_seconds = time.perf_counter() - store_start
            ingest_seconds = time.perf_counter() - start
            reload_start = time.perf_counter()
            store.upsert(strategy, chunks, vectors)
            after = store.count(strategy)
            if before != after or after != len(chunks):
                raise RuntimeError("Reingest duplicate check failed")
            resources.append({"strategy": strategy, "chunks": len(chunks), "min_chars": min(len(c.text) for c in chunks),
                "median_chars": statistics.median(len(c.text) for c in chunks), "max_chars": max(len(c.text) for c in chunks),
                "total_chars": sum(len(c.text) for c in chunks), "total_tokens": sum(token_lengths),
                "truncated_chunks": sum(n > embedder.model.max_seq_length for n in token_lengths),
                "embedding_seconds": vector_seconds, "store_seconds": store_seconds, "ingest_seconds": ingest_seconds,
                "reingest_seconds": time.perf_counter() - reload_start, "count_before": before, "count_after": after,
                "embedding_reused_from": "B" if strategy == "C" else None, "api_cost_usd": 0})
            write_jsonl(out / f"chunks_{strategy}.jsonl", [asdict(c) for c in chunks])
        # Reopen store to verify persistence BEFORE any retrieval.
        store.close()
        store = QdrantStore(ROOT / ".qdrant", embedder.dimensions)
        for r in resources:
            r["count_after_reopen"] = store.count(r["strategy"])
            if r["count_after_reopen"] != r["chunks"]:
                raise RuntimeError("Persistence check failed")
        query_vectors = dict(zip([q["id"] for q in questions], embedder.embed_documents([q["question"] for q in questions])))
        traces = []
        for split in ("dev", "test"):
            for strategy in "ABC":
                for q in questions:
                    if q["split"] != split:
                        continue
                    filters = q.get("filter", {}) if config[strategy]["filter"] else {}
                    start = time.perf_counter()
                    # Only question text and user-supplied filter reach retrieval.
                    hits = store.search(strategy, query_vectors[q["id"]], filters=filters)
                    traces.append({**evaluate_query(q, hits), "strategy": strategy, "applied_filter": filters,
                                   "search_seconds": time.perf_counter() - start})
            if split == "dev":
                dev = summarize(traces)
                counts = {r["strategy"]: r["chunks"] for r in resources}
                winner = sorted(dev, key=lambda r: (-r["hit3"], -r["hit1"], counts[r["strategy"]], r["strategy"]))[0]["strategy"]
                write_json(out / "selection.json", {"selected_strategy": winner, "selected_at": datetime.now(timezone.utc).isoformat(),
                    "criterion": config["selection"], "dev_metrics": dev, "test_evaluated_at_selection": False})
                write_jsonl(out / "traces_dev.jsonl", traces)
        write_jsonl(out / "traces.jsonl", traces)
        write_json(out / "metrics.json", summarize(traces))
        write_csv(out / "metrics.csv", summarize(traces))
        write_json(out / "resources.json", resources)
        audit_samples(out, pages, chunks_by_strategy, traces)
        versions = {name: importlib.metadata.version(name) for name in ("torch", "sentence-transformers", "transformers", "qdrant-client", "pypdf", "huggingface-hub", "numpy")}
        write_json(out / "environment.json", {"python": platform.python_version(), "platform": platform.platform(), "libraries": versions,
            "model": config["model"], "revision": config["revision"], "dimensions": embedder.dimensions, "device": "cpu",
            "max_seq_length": embedder.model.max_seq_length, "model_load_seconds": load_seconds,
            "embedding_processing": "Same model, mean pooling and L2 normalization for queries/documents; no prefixes; batch 32",
            "store": "Qdrant local persistent", "store_path": ".qdrant", "metric": "cosine", "search": "exact",
            "api_cost_usd": 0, "cost_scope": "No paid API calls; electricity/hardware/network excluded", "human_audit": "pending"})
        write_json(ROOT / "results/latest.json", {"run_directory": out.relative_to(ROOT).as_posix()})
        print(json.dumps(summarize(traces), indent=2))
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ROOT / "results/runs" / stamp
    out.mkdir(parents=True)
    logging.basicConfig(filename=out / "errors.log", level=logging.INFO, encoding="utf-8", force=True)
    try:
        run(args, out)
    except Exception:
        logging.exception("Pipeline failed; no mock fallback")
        write_json(out / "failure.json", {"status": "failed", "error_type": __import__("sys").exc_info()[0].__name__, "see": "errors.log"})
        raise


if __name__ == "__main__":
    main()
