from app.retrieval.base import BaseRetriever, tokenize
from app.schema.models import RetrievalCandidate


class BM25Retriever(BaseRetriever):
    def __init__(self, candidates: list[RetrievalCandidate]) -> None:
        self.candidates = candidates
        self.tokenized = [tokenize(candidate.text) for candidate in candidates]
        try:
            from rank_bm25 import BM25Okapi

            self.index = BM25Okapi(self.tokenized)
        except ImportError:
            self.index = None

    def retrieve(self, query: str, top_k: int) -> list[RetrievalCandidate]:
        tokens = tokenize(query)
        if not tokens:
            return []
        if self.index is not None:
            scores = self.index.get_scores(tokens)
        else:
            query_terms = set(tokens)
            scores = [len(query_terms.intersection(doc_tokens)) for doc_tokens in self.tokenized]

        ranked = sorted(enumerate(scores), key=lambda item: float(item[1]), reverse=True)[:top_k]
        results: list[RetrievalCandidate] = []
        for idx, score in ranked:
            if float(score) <= 0:
                continue
            candidate = self.candidates[idx].model_copy(update={"score": float(score), "source": "bm25"})
            results.append(candidate)
        return results
