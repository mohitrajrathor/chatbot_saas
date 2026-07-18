from sentence_transformers import SentenceTransformer
from app.core.config import settings


class EmbeddingModel:
    def __init__(self, model_name: str | None = None):
        name = model_name or settings.EMBEDDING_MODEL
        self.model = SentenceTransformer(name)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding.tolist()


# Module-level singleton instance loaded once at startup
_embedder_instance: EmbeddingModel | None = None


def get_embedder() -> EmbeddingModel:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = EmbeddingModel()
    return _embedder_instance
