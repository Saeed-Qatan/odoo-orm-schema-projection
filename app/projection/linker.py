from app.schema.models import QueryUnderstanding, RetrievalCandidate


class SchemaLinker:
    def link(
        self,
        candidates: list[RetrievalCandidate],
        understanding: QueryUnderstanding | None = None,
    ) -> tuple[set[str], dict[str, set[str]], dict[str, float]]:
        confidence = {candidate.id: candidate.score for candidate in candidates}

        if understanding and (understanding.required_models or understanding.required_fields):
            models = set(understanding.required_models)
            fields = {
                model: set(model_fields)
                for model, model_fields in understanding.required_fields.items()
            }
            for model in fields:
                models.add(model)
            return models, fields, confidence

        models: set[str] = set()
        fields: dict[str, set[str]] = {}

        for candidate in candidates:
            models.add(candidate.model)
            if candidate.kind == "field" and candidate.field:
                fields.setdefault(candidate.model, set()).add(candidate.field)

        return models, fields, confidence
