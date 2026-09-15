from app.schema.models import RetrievalCandidate


class SchemaLinker:
    def link(self, candidates: list[RetrievalCandidate]) -> tuple[set[str], dict[str, set[str]], dict[str, float]]:
        models: set[str] = set()
        fields: dict[str, set[str]] = {}
        confidence: dict[str, float] = {}

        for candidate in candidates:
            models.add(candidate.model)
            confidence[candidate.id] = candidate.score
            if candidate.kind == "field" and candidate.field:
                fields.setdefault(candidate.model, set()).add(candidate.field)

        return models, fields, confidence
