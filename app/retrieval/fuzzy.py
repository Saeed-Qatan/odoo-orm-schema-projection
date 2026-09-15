from app.retrieval.base import BaseRetriever, normalize_text
from app.schema.models import RetrievalCandidate


class FuzzyRetriever(BaseRetriever):
    def __init__(self, candidates: list[RetrievalCandidate]) -> None:
        self.candidates = candidates
        try:
            from rapidfuzz import fuzz

            self.fuzz = fuzz
        except ImportError:
            self.fuzz = None

    def retrieve(self, query: str, top_k: int) -> list[RetrievalCandidate]:
        normalized_query = normalize_text(query)
        scored: list[RetrievalCandidate] = []
        for candidate in self.candidates:
            if self.fuzz is not None:
                score = self.fuzz.partial_ratio(normalized_query, normalize_text(candidate.text)) / 100
            else:
                score = 1.0 if normalized_query in normalize_text(candidate.text) else 0.0
            if score >= 0.55:
                scored.append(candidate.model_copy(update={"score": float(score), "source": "fuzzy"}))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]
