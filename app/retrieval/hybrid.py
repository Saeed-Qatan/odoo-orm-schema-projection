from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.fuzzy import FuzzyRetriever
from app.retrieval.rrf import reciprocal_rank_fusion
from app.schema.models import RetrievalCandidate


class HybridRetriever:
    def __init__(
        self,
        candidates: list[RetrievalCandidate],
        embedding_model: str,
        enable_dense: bool,
    ) -> None:
        self.bm25 = BM25Retriever(candidates)
        self.fuzzy = FuzzyRetriever(candidates)
        self.dense = DenseRetriever(candidates, embedding_model, enabled=enable_dense)

    def retrieve(self, query: str, top_k_bm25: int, top_k_dense: int, top_k_final: int) -> list[RetrievalCandidate]:
        bm25 = self.bm25.retrieve(query, top_k_bm25)
        fuzzy = self.fuzzy.retrieve(query, top_k_bm25)
        dense = self.dense.retrieve(query, top_k_dense)
        return reciprocal_rank_fusion([bm25, fuzzy, dense])[:top_k_final]
