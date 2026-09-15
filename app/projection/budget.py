from dataclasses import dataclass

from app.core.config import Settings
from app.schema.models import ProjectionOptions


@dataclass(frozen=True)
class RetrievalBudget:
    max_models: int
    max_depth: int
    max_fields_per_model: int
    max_total_fields: int
    top_k_bm25: int
    top_k_dense: int
    top_k_final: int


class BudgetRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def route(self, query: str, options: ProjectionOptions) -> RetrievalBudget:
        complexity_boost = 1 if len(query.split()) >= 10 else 0
        return RetrievalBudget(
            max_models=min(options.max_models or self.settings.default_max_models + complexity_boost, 8),
            max_depth=min(options.max_depth or self.settings.default_max_depth, 4),
            max_fields_per_model=min(options.max_fields_per_model or self.settings.default_max_fields_per_model, 12),
            max_total_fields=min(options.max_total_fields or self.settings.default_max_total_fields, 50),
            top_k_bm25=self.settings.top_k_bm25,
            top_k_dense=self.settings.top_k_dense,
            top_k_final=options.top_k_final or self.settings.top_k_final,
        )
