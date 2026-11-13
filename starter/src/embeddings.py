"""Real local embedding adapter. Provider errors propagate without fallback."""
from typing import Protocol


class Embedder(Protocol):
    model_name: str
    dimensions: int
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, question: str) -> list[float]: ...


class MyEmbedder:
    def __init__(self, model_name: str, revision=None, cache_folder=None):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, revision=revision, cache_folder=cache_folder, device="cpu")
        self.dimensions = self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts):
        if not texts:
            return []
        return self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True).tolist()

    def embed_query(self, question):
        return self.embed_documents([question])[0]
