"""Strict single-chunk evidence metrics, separate from manual labels."""
from collections import defaultdict
from .ingestion import normalize_text


def evidence_key(text):
    return " ".join(normalize_text(text).split())


def golds(question):
    return [{"source_id": question["gold_source_id"], "page": question["gold_page"],
             "evidence_quote": question["evidence_quote"]}, *question.get("alternative_gold", [])]


def evaluate_query(question, hits):
    checks = [any(hit["metadata"]["document_id"] == g["source_id"]
                  and hit["metadata"]["page"] == g["page"]
                  and evidence_key(g["evidence_quote"]) in evidence_key(hit["text"])
                  for g in golds(question)) for hit in hits[:3]]
    return {**question, "hits": hits[:3], "evidence_hits": checks,
            "hit1": bool(checks and checks[0]), "hit3": any(checks)}


def summarize(traces):
    groups = defaultdict(list)
    for trace in traces:
        groups[(trace["strategy"], trace["split"])].append(trace)
    return [{"strategy": s, "split": split, "n": len(rows),
             "hit1_count": sum(r["hit1"] for r in rows), "hit3_count": sum(r["hit3"] for r in rows),
             "hit1": sum(r["hit1"] for r in rows) / len(rows),
             "hit3": sum(r["hit3"] for r in rows) / len(rows)}
            for (s, split), rows in sorted(groups.items())]
