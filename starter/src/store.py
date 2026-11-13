"""Persistent Qdrant local store; exact cosine and payload filters."""
import math
import uuid
from dataclasses import asdict

ALLOWED_FILTERS = {"chapter", "language"}


class QdrantStore:
    def __init__(self, path, dimensions):
        from qdrant_client import QdrantClient
        if dimensions <= 0:
            raise ValueError("Invalid dimensions")
        self.client = QdrantClient(path=str(path))
        self.dimensions = dimensions

    def create_schema(self):
        """Collections are created per strategy by upsert."""

    def _validate(self, vector):
        if len(vector) != self.dimensions or not all(math.isfinite(x) for x in vector) or not any(vector):
            raise ValueError("Non-finite, zero or incompatible vector")

    def upsert(self, strategy, chunks, vectors):
        """Replace complete strategy snapshot to remove obsolete chunks.

        All vectors validated before mutation. Single writer; replacement is not
        crash-atomic, and an interrupted ingestion must be re-run.
        """
        from qdrant_client import models
        if strategy not in {"A", "B", "C"} or len(chunks) != len(vectors):
            raise ValueError("Invalid strategy/vector count")
        if len({c.chunk_id for c in chunks}) != len(chunks):
            raise ValueError("Duplicate chunk IDs")
        for vector in vectors:
            self._validate(vector)
        name = f"day6_{strategy}"
        if self.client.collection_exists(name):
            self.client.delete_collection(name)
        self.client.create_collection(name, vectors_config=models.VectorParams(size=self.dimensions, distance=models.Distance.COSINE))
        for offset in range(0, len(chunks), 128):
            points = []
            for chunk, vector in zip(chunks[offset:offset+128], vectors[offset:offset+128]):
                value = asdict(chunk)
                payload = {**value.pop("metadata"), **value}
                points.append(models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)), vector=vector, payload=payload))
            self.client.upsert(name, points=points, wait=True)

    def search(self, strategy, query_vector, top_k=3, filters=None):
        from qdrant_client import models
        self._validate(query_vector)
        if strategy not in {"A", "B", "C"} or top_k <= 0:
            raise ValueError("Invalid strategy/top_k")
        if set(filters or {}) - ALLOWED_FILTERS:
            raise ValueError("Unsupported filter; gold/source IDs cannot be filters")
        conditions = [models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in (filters or {}).items()]
        result = self.client.query_points(f"day6_{strategy}", query=query_vector, limit=top_k,
            query_filter=models.Filter(must=conditions) if conditions else None,
            search_params=models.SearchParams(exact=True), with_payload=True)
        return [{"chunk_id": p.payload["chunk_id"], "text": p.payload["text"], "score": p.score,
                 "metadata": {k: v for k, v in p.payload.items() if k not in {"text", "chunk_id"}}} for p in result.points]

    def count(self, strategy):
        return self.client.count(f"day6_{strategy}", exact=True).count

    def close(self):
        self.client.close()
