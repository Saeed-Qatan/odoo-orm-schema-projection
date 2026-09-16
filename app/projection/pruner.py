from app.projection.budget import RetrievalBudget
from app.schema.models import OrmSchema


class SchemaPruner:
    def prune(
        self,
        schema: OrmSchema,
        selected_models: set[str],
        selected_fields: dict[str, set[str]],
        relation_fields: dict[str, set[str]],
        budget: RetrievalBudget,
    ) -> tuple[dict[str, set[str]], list[str]]:
        pruned: dict[str, set[str]] = {}
        removed: list[str] = []
        total = 0

        for model_name in list(selected_models)[: budget.max_models]:
            model = schema.models.get(model_name)
            if not model:
                continue

            requested = set(selected_fields.get(model_name, set()))
            requested.update(relation_fields.get(model_name, set()))

            if not requested:
                if "name" in model.fields:
                    requested.add("name")
                elif "id" in model.fields:
                    requested.add("id")

            clean_fields = [field for field in requested if field in model.fields]

            clean_fields = clean_fields[: budget.max_fields_per_model]
            allowed_count = max(0, budget.max_total_fields - total)
            clean_fields = clean_fields[:allowed_count]
            total += len(clean_fields)
            pruned[model_name] = set(clean_fields)

            for field_name in model.fields:
                if field_name not in pruned[model_name]:
                    removed.append(f"{model_name}.{field_name}")

            if total >= budget.max_total_fields:
                break

        return pruned, removed

