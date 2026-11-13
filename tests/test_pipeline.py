"""Contract regressions: evidence, chunk coverage, durable replacement/filtering."""
import tempfile
import unittest
from pathlib import Path
from starter.src.chunking import by_paragraph, fixed_size
from starter.src.evaluation import evaluate_query, summarize
from starter.src.ingestion import normalize_text
from starter.src.models import DocumentPage
from starter.src.run import validate, read_questions
from starter.src.ingestion import load_jsonl
from starter.src.prepare import ROOT
from starter.src.store import QdrantStore


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.page = DocumentPage("doc", "source", 1, "First sentence.\n\n" + "A long paragraph with words. " * 100,
                                 {"chapter": 1, "language": "en"})

    def test_normalization_preserves_structure_and_unicode(self):
        self.assertEqual(normalize_text("  Cafe\u0301\r\n next\r\n\r\n para\t words "), "Café next\n\npara words")

    def test_chunk_coverage_offsets_and_stability(self):
        for chunker in (lambda p: fixed_size(p, 100, 10), lambda p: by_paragraph(p, 100)):
            chunks = chunker(self.page)
            self.assertEqual([c.chunk_id for c in chunks], [c.chunk_id for c in chunker(self.page)])
            covered = set()
            for c in chunks:
                start, end = c.metadata["start"], c.metadata["end"]
                self.assertEqual(c.text, self.page.text[start:end])
                self.assertLessEqual(len(c.text), 100)
                covered.update(range(start, end))
            self.assertTrue(all(i in covered for i, char in enumerate(self.page.text) if not char.isspace()))
        for size, overlap in [(0, 0), (10, 10), (10, -1)]:
            with self.assertRaises(ValueError):
                fixed_size(self.page, size, overlap)

    def test_strict_hit_and_alternative_gold(self):
        q = {"id": "q", "gold_source_id": "doc", "gold_page": 1, "evidence_quote": "full evidence required"}
        def hit(doc, page, text):
            return {"metadata": {"document_id": doc, "page": page}, "text": text}
        partial = hit("doc", 1, "full evidence")
        wrong_page = hit("doc", 2, "full evidence required")
        valid = hit("doc", 1, "prefix full\n evidence required suffix")
        result = evaluate_query(q, [partial, wrong_page, valid])
        self.assertFalse(result["hit1"])
        self.assertTrue(result["hit3"])
        self.assertFalse(evaluate_query(q, []) ["hit3"])
        q["alternative_gold"] = [{"source_id": "other", "page": 8, "evidence_quote": "another valid quote"}]
        self.assertTrue(evaluate_query(q, [hit("other", 8, "another valid quote")])["hit1"])
        rows = summarize([{**result, "strategy": "A", "split": "test"}])
        self.assertEqual((rows[0]["hit1_count"], rows[0]["hit3_count"], rows[0]["n"]), (0, 1, 1))

    def test_persistent_snapshot_replaces_stale_chunks_and_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            store = QdrantStore(directory, 2)
            chunks = fixed_size(self.page, 100, 0)[:2]
            chunks[1].metadata["chapter"] = 2
            store.upsert("A", chunks, [[1.0, 0.0], [0.0, 1.0]])
            store.upsert("A", chunks, [[1.0, 0.0], [0.0, 1.0]])
            self.assertEqual(store.count("A"), 2)
            found = store.search("A", [1.0, 0.0], filters={"chapter": 2})
            self.assertEqual(found[0]["metadata"]["chapter"], 2)
            with self.assertRaises(ValueError):
                store.search("A", [1.0, 0.0], filters={"gold_source_id": "doc"})
            with self.assertRaises(ValueError):
                store.upsert("A", chunks, [[1.0, 0.0]])
            self.assertEqual(store.count("A"), 2)
            store.upsert("A", chunks[:1], [[1.0, 0.0]])
            store.close()
            store = QdrantStore(directory, 2)
            self.assertEqual(store.count("A"), 1)
            self.assertEqual(store.search("A", [1.0, 0.0])[0]["chunk_id"], chunks[0].chunk_id)
            store.close()

    def test_frozen_corpus_and_benchmark(self):
        validate(load_jsonl(ROOT / "data/pages.jsonl"), read_questions())


    def test_human_audit_rejects_ai_or_pending_labels(self):
        from starter.src.audit import summarize_human
        with self.assertRaises(ValueError):
            summarize_human(ROOT / "results/baseline")


if __name__ == "__main__":
    unittest.main()
