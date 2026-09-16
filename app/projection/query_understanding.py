from app.retrieval.base import normalize_text, tokenize
from app.schema.aliases import AliasCatalog, get_alias_catalog
from app.schema.models import QueryUnderstanding


class QueryIntentResolver:
    def __init__(self, aliases: AliasCatalog) -> None:
        self.aliases = aliases

    def resolve(self, tokens: set[str]) -> str | None:
        for intent, terms in self.aliases.intent_terms.items():
            if tokens & {normalize_text(term) for term in terms}:
                return intent
        return None


class EntityResolver:
    def __init__(self, aliases: AliasCatalog) -> None:
        self.aliases = aliases

    def resolve(self, tokens: set[str]) -> list[str]:
        entities: list[str] = []
        for entity, config in self.aliases.entities.items():
            terms = {normalize_text(term) for term in config.get("terms", [])}
            if tokens & terms:
                entities.append(entity)
        return entities


class QueryUnderstandingExtractor:
    def __init__(self, aliases: AliasCatalog | None = None) -> None:
        self.aliases = aliases or get_alias_catalog()
        self.intent_resolver = QueryIntentResolver(self.aliases)
        self.entity_resolver = EntityResolver(self.aliases)

    def understand(self, query: str) -> QueryUnderstanding:
        normalized = normalize_text(query)
        tokens = set(tokenize(normalized))
        intent = self.intent_resolver.resolve(tokens)
        entities = self.entity_resolver.resolve(tokens)
        filters: dict[str, str] = {}
        required_models: list[str] = []
        required_fields: dict[str, list[str]] = {}

        def add_model(model: str) -> None:
            if model not in required_models:
                required_models.append(model)

        def add_field(model: str, field: str) -> None:
            add_model(model)
            required_fields.setdefault(model, [])
            if field not in required_fields[model]:
                required_fields[model].append(field)

        def merge_required(config: dict) -> None:
            for model in config.get("required_models", []):
                add_model(model)
            for model, fields in config.get("required_fields", {}).items():
                for field in fields:
                    add_field(model, field)

        if intent == "sales_analysis":
            add_model("sale.order")
            if "sales" not in entities:
                entities.insert(0, "sales")

        for entity in entities:
            merge_required(self.aliases.entities.get(entity, {}))

        month = self._month(normalized)
        if month:
            if "date" not in entities:
                entities.append("date")
            filters["month"] = month
            add_field("sale.order", "date_order")

        for filter_name, config in self.aliases.filters.items():
            terms = {normalize_text(term) for term in config.get("terms", [])}
            if tokens & terms:
                filters[filter_name] = config.get("value", filter_name)
                merge_required(config)

        anchor_model = "sale.order" if intent == "sales_analysis" else (required_models[0] if required_models else None)
        return QueryUnderstanding(
            intent=intent,
            entities=entities,
            filters=filters,
            required_models=required_models,
            required_fields=required_fields,
            anchor_model=anchor_model,
        )

    def _month(self, normalized_query: str) -> str | None:
        for term, month in self.aliases.months.items():
            if normalize_text(term) in normalized_query:
                return month
        return None
