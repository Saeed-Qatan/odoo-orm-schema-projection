from rapidfuzz import fuzz

from app.retrieval.base import normalize_text, tokenize
from app.schema.aliases import AliasCatalog, get_alias_catalog
from app.schema.models import MatchedTerm, OrmSchema, QueryUnderstanding


class QueryIntentResolver:
    def __init__(self, aliases: AliasCatalog) -> None:
        self.aliases = aliases

    def resolve(self, tokens: set[str], normalized_query: str) -> str | None:
        for intent, terms in self.aliases.intent_terms.items():
            for term in terms:
                normalized_term = normalize_text(term)
                if normalized_term in tokens or normalized_term in normalized_query:
                    return intent
        return None


class EntityResolver:
    def __init__(self, aliases: AliasCatalog) -> None:
        self.aliases = aliases

    def resolve(self, tokens: set[str], normalized_query: str) -> tuple[list[str], list[MatchedTerm]]:
        entities: list[str] = []
        matches: list[MatchedTerm] = []
        for entity, config in self.aliases.entities.items():
            terms = [str(term) for term in config.get("terms", [])]
            normalized_terms = [(term, normalize_text(term)) for term in terms]
            if self._has_exact_match(tokens, normalized_query, normalized_terms):
                entities.append(entity)
                continue
            fuzzy_match = self._best_fuzzy_match(tokens, normalized_terms, entity)
            if fuzzy_match:
                entities.append(entity)
                matches.append(fuzzy_match)
        return entities, matches

    def _has_exact_match(
        self,
        tokens: set[str],
        normalized_query: str,
        normalized_terms: list[tuple[str, str]],
    ) -> bool:
        return any(
            term in tokens if " " not in term else term in normalized_query
            for _original, term in normalized_terms
        )

    def _best_fuzzy_match(
        self,
        tokens: set[str],
        normalized_terms: list[tuple[str, str]],
        target: str,
    ) -> MatchedTerm | None:
        best: MatchedTerm | None = None
        for token in tokens:
            if len(token) < 4:
                continue
            for original, term in normalized_terms:
                if len(term) < 4:
                    continue
                score = fuzz.ratio(token, term) / 100
                threshold = 0.88
                if score < threshold:
                    continue
                if best is None or score > best.score:
                    best = MatchedTerm(
                        input=token,
                        matched=original,
                        target=target,
                        score=round(float(score), 4),
                        match_type="fuzzy",
                    )
        return best


class QueryUnderstandingExtractor:
    def __init__(
        self, aliases: AliasCatalog | None = None, schema: OrmSchema | None = None
    ) -> None:
        self.aliases = aliases or get_alias_catalog()
        self.schema = schema
        self.intent_resolver = QueryIntentResolver(self.aliases)
        self.entity_resolver = EntityResolver(self.aliases)

    def understand(self, query: str) -> QueryUnderstanding:
        normalized = normalize_text(query)
        tokens = set(tokenize(normalized))
        intent = self.intent_resolver.resolve(tokens, normalized)
        entities, matched_terms = self.entity_resolver.resolve(tokens, normalized)
        filters: dict[str, str] = {}
        required_models: list[str] = []
        required_fields: dict[str, list[str]] = {}
        field_paths: list[list[str]] = []

        def add_model(model: str) -> None:
            if model not in required_models:
                required_models.append(model)

        def add_field(model: str, field: str) -> None:
            add_model(model)
            required_fields.setdefault(model, [])
            if field not in required_fields[model]:
                required_fields[model].append(field)

        def merge_required(config: dict) -> None:
            if self.schema is not None:
                for variant in config.get("schema_variants", []):
                    requirements = variant.get("required_fields", {})
                    if requirements and all(
                        model in self.schema.models
                        and all(field in self.schema.models[model].fields for field in fields)
                        for model, fields in requirements.items()
                    ):
                        config = variant
                        break
            configured_paths = config.get("field_paths", [])
            if self.schema is not None and intent == "sales_analysis":
                valid_paths = []
                for path in configured_paths:
                    model_name = path[0]
                    resolved = []
                    for index, field_name in enumerate(path[1:]):
                        model = self.schema.models.get(model_name)
                        field = model.fields.get(field_name) if model else None
                        if not field:
                            break
                        resolved.append((model_name, field_name))
                        if index < len(path) - 2:
                            if not field.relation:
                                break
                            model_name = field.relation
                    else:
                        valid_paths.append((path, resolved))
                if configured_paths and not valid_paths:
                    return
                for path, resolved in valid_paths:
                    if path not in field_paths:
                        field_paths.append(path)
                    for model_name, field_name in resolved:
                        add_field(model_name, field_name)
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
            if intent == "sales_analysis" and self.schema is not None:
                field_paths.append(["sale.order", "date_order"])

        if intent == "sales_analysis" or entities:
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
            field_paths=field_paths,
            matched_terms=matched_terms,
        )

    def _month(self, normalized_query: str) -> str | None:
        for term, month in self.aliases.months.items():
            if normalize_text(term) in normalized_query:
                return month
        return None
