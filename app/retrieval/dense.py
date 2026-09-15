from app.retrieval.base import BaseRetriever
from app.schema.models import RetrievalCandidate


class DenseRetriever(BaseRetriever):
    def __init__(self, candidates: list[RetrievalCandidate], model_name: str, enabled: bool = False) -> None:
        self.candidates = candidates
        self.enabled = enabled
        self.model_name = model_name
        self.model = None
        self.embeddings = None
        self.index = None
        if enabled:
            self._load()

    def _load(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)
            self.embeddings = self.model.encode(
                [candidate.text for candidate in self.candidates],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            try:
                import faiss

                self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
                self.index.add(self.embeddings)
            except Exception:
                self.index = None
        except Exception:
            self.model = None
            self.embeddings = None
            self.index = None

    def retrieve(self, query: str, top_k: int) -> list[RetrievalCandidate]:
        if not self.enabled or self.model is None or self.embeddings is None:
            return []
        query_embedding = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
        if self.index is not None:
            scores, indexes = self.index.search(query_embedding.reshape(1, -1), top_k)
            ranked = [(int(idx), float(score)) for idx, score in zip(indexes[0], scores[0]) if idx >= 0]
        else:
            scores = self.embeddings @ query_embedding
            ranked = sorted(enumerate(scores), key=lambda item: float(item[1]), reverse=True)[:top_k]
        return [
            self.candidates[idx].model_copy(update={"score": float(score), "source": "dense"})
            for idx, score in ranked
            if float(score) > 0
        ]
