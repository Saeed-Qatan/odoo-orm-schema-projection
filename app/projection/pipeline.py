from time import perf_counter

from app.core.config import Settings
from app.graph.builder import SchemaGraphBuilder
from app.graph.traverser import GraphTraverser
from app.projection.budget import BudgetRouter
from app.projection.linker import SchemaLinker
from app.projection.projector import SchemaProjector
from app.projection.query_understanding import QueryUnderstandingExtractor
from app.projection.pruner import SchemaPruner
from app.retrieval.base import build_corpus, normalize_text
from app.retrieval.hybrid import HybridRetriever
from app.schema.models import ConfidenceScores, OrmSchema, ProjectionDebug, ProjectionMetrics, ProjectionOptions, ProjectionResponse, RelationshipPath


class SchemaProjectionPipeline:
    def __init__(self, schema: OrmSchema, settings: Settings) -> None:
        self.schema = schema
        self.settings = settings
        self.graph = SchemaGraphBuilder().build(schema)
        self.traverser = GraphTraverser(self.graph, schema)
        self.retriever = HybridRetriever(
            build_corpus(schema),
            embedding_model=settings.embedding_model,
            enable_dense=settings.enable_dense_retrieval,
        )
        self.budget_router = BudgetRouter(settings)
        self.linker = SchemaLinker()
        self.pruner = SchemaPruner()
        self.projector = SchemaProjector()
        self.query_understanding = QueryUnderstandingExtractor(schema=schema)

    def run(self, query: str, options: ProjectionOptions) -> ProjectionResponse:
        started = perf_counter()
        normalized_query = normalize_text(query)
        understanding = self.query_understanding.understand(query)
        budget = self.budget_router.route(normalized_query, options)

        retrieval_started = perf_counter()
        candidates = self.retriever.retrieve(
            normalized_query,
            top_k_bm25=budget.top_k_bm25,
            top_k_dense=budget.top_k_dense,
            top_k_final=budget.top_k_final,
        )
        retrieval_ms = (perf_counter() - retrieval_started) * 1000

        if not self._is_supported_query(understanding, candidates, normalized_query):
            return self._unsupported_response(
                query=query,
                understanding=understanding,
                candidates=candidates,
                retrieval_ms=retrieval_ms,
                started=started,
                debug_enabled=options.debug,
            )

        linked_models, linked_fields, _confidence = self.linker.link(candidates, understanding)
        anchor_model = understanding.anchor_model or self._anchor_model(candidates, linked_models)

        graph_started = perf_counter()
        explicit_relationships = None
        active_field_paths = []
        if understanding.field_paths:
            active_field_paths = [
                path for path in understanding.field_paths if len(path) - 2 <= budget.max_depth
            ]
            linked_models, linked_fields, paths, explicit_relationships = self._connect_field_paths(active_field_paths)
            if not linked_models and anchor_model in self.schema.models:
                linked_models = {anchor_model}
            connected_models = linked_models
            relation_fields = {}
        else:
            connected_models, relation_fields, paths = self._connect_from_anchor(anchor_model, linked_models, budget.max_depth)
        selected_model_set = self._filter_allowed_models(linked_models, connected_models, paths) & set(self.schema.models)
        selected_models = self._ordered_models(anchor_model, selected_model_set, candidates)
        graph_ms = (perf_counter() - graph_started) * 1000

        projection_started = perf_counter()
        pruned_fields, removed_fields = self.pruner.prune(
            self.schema,
            selected_models,
            linked_fields,
            relation_fields,
            budget,
        )
        safe_fields, hallucinated_models, hallucinated_fields = self._validate(pruned_fields)
        if understanding.field_paths:
            retained_paths = []
            for path in active_field_paths:
                current = path[0]
                for index, name in enumerate(path[1:]):
                    if name not in safe_fields.get(current, set()):
                        break
                    if index < len(path) - 2:
                        current = self.schema.models[current].fields[name].relation
                else:
                    retained_paths.append(path)
            _, retained_fields, paths, explicit_relationships = self._connect_field_paths(retained_paths)
            safe_fields = {
                model: retained_fields[model] for model in safe_fields if model in retained_fields
            }
            if not safe_fields and anchor_model in self.schema.models:
                safe_fields = {anchor_model: set()}
            active_field_paths = retained_paths
            removed_fields = [
                f"{model}.{name}" for model in selected_models
                for name in self.schema.models[model].fields
                if name not in safe_fields.get(model, set())
            ]
        projected = self.projector.project(self.schema, safe_fields, preferred_roots=[anchor_model] if anchor_model else None, field_paths=active_field_paths if understanding.field_paths else None)
        projection_ms = (perf_counter() - projection_started) * 1000

        total_fields_before = sum(len(model.fields) for model in self.schema.models.values())
        total_fields_after = sum(len(fields) for fields in safe_fields.values())
        reduction_ratio = 1 - (total_fields_after / total_fields_before) if total_fields_before else 0
        latency_ms = (perf_counter() - started) * 1000

        metrics = ProjectionMetrics(
            latency_ms=round(latency_ms, 3),
            retrieval_ms=round(retrieval_ms, 3),
            graph_ms=round(graph_ms, 3),
            projection_ms=round(projection_ms, 3),
            total_fields_before=total_fields_before,
            total_fields_after=total_fields_after,
            reduction_ratio=round(reduction_ratio, 4),
            hallucinated_models=hallucinated_models,
            hallucinated_fields=hallucinated_fields,
        )

        debug = None
        if options.debug:
            debug = ProjectionDebug(
                query_understanding=understanding,
                retrieval=candidates,
                paths=paths,
                relationship_paths=explicit_relationships if explicit_relationships is not None else self._relationship_paths(paths),
                removed_fields=removed_fields,
                confidence=self._confidence(candidates, linked_fields, paths),
                metrics=metrics,
            )

        return ProjectionResponse(query=query, models=list(safe_fields.keys()), schema=projected, debug=debug)

    def _is_supported_query(
        self,
        understanding,
        candidates: list,
        normalized_query: str,
    ) -> bool:
        if (
            understanding.intent
            or understanding.entities
            or understanding.filters
            or understanding.required_models
            or understanding.required_fields
            or understanding.field_paths
        ):
            return True

        best_score = max((float(candidate.score) for candidate in candidates), default=0.0)
        has_schema_literal = "." in normalized_query or "_" in normalized_query
        return has_schema_literal and best_score >= 0.85

    def _unsupported_response(
        self,
        query: str,
        understanding,
        candidates: list,
        retrieval_ms: float,
        started: float,
        debug_enabled: bool,
    ) -> ProjectionResponse:
        total_fields_before = sum(len(model.fields) for model in self.schema.models.values())
        metrics = ProjectionMetrics(
            latency_ms=round((perf_counter() - started) * 1000, 3),
            retrieval_ms=round(retrieval_ms, 3),
            graph_ms=0,
            projection_ms=0,
            total_fields_before=total_fields_before,
            total_fields_after=0,
            reduction_ratio=1.0 if total_fields_before else 0,
            hallucinated_models=0,
            hallucinated_fields=0,
        )
        debug = None
        if debug_enabled:
            debug = ProjectionDebug(
                query_understanding=understanding,
                retrieval=candidates,
                paths=[],
                relationship_paths=[],
                removed_fields=[],
                confidence=self._confidence(candidates, {}, []),
                metrics=metrics,
            )
        return ProjectionResponse(
            query=query,
            supported=False,
            unsupported_reason="Query is outside the supported Odoo schema projection domain.",
            models=[],
            schema={},
            debug=debug,
        )

    def _connect_field_paths(
        self, field_paths: list[list[str]]
    ) -> tuple[set[str], dict[str, set[str]], list[list[str]], list[RelationshipPath]]:
        models: set[str] = set()
        fields: dict[str, set[str]] = {}
        paths: list[list[str]] = []
        relationships: list[RelationshipPath] = []
        for field_path in field_paths:
            current = field_path[0]
            model_path = [current]
            relation_names: dict[str, str] = {}
            for index, name in enumerate(field_path[1:]):
                field = self.schema.models[current].fields[name]
                models.add(current)
                fields.setdefault(current, set()).add(name)
                if index < len(field_path) - 2:
                    relation_names[current] = name
                    current = field.relation
                    model_path.append(current)
            for length in range(2, len(model_path) + 1):
                prefix = model_path[:length]
                if prefix not in paths:
                    paths.append(prefix)
                    relationships.append(RelationshipPath(
                        models=prefix,
                        relation_fields={model: relation_names[model] for model in prefix[:-1]},
                    ))
        paths.sort(key=lambda path: (len(path), path[-1]))
        return models, fields, paths, relationships

    def _anchor_model(self, candidates: list, linked_models: set[str]) -> str | None:
        for candidate in candidates:
            if candidate.kind == "model" and candidate.model in linked_models:
                return candidate.model
        for candidate in candidates:
            if candidate.model in linked_models:
                return candidate.model
        return next(iter(linked_models), None)

    def _connect_from_anchor(
        self,
        anchor_model: str | None,
        linked_models: set[str],
        max_depth: int,
    ) -> tuple[set[str], dict[str, set[str]], list[list[str]]]:
        if not anchor_model:
            return self.traverser.connect_models(linked_models, max_depth)

        selected = set(linked_models)
        relation_fields: dict[str, set[str]] = {}
        paths: list[list[str]] = []
        for target in linked_models:
            if target == anchor_model:
                continue
            path = self.traverser.shortest_model_path(anchor_model, target)
            if not path or len(path) - 1 > max_depth:
                continue
            paths.append(path)
            selected.update(path)
            for model, fields in self.traverser.relation_fields_for_path(path).items():
                relation_fields.setdefault(model, set()).update(fields)

        paths.sort(key=lambda path: (len(path), path[-1] if path else ""))
        return selected, relation_fields, paths

    def _filter_allowed_models(
        self,
        linked_models: set[str],
        connected_models: set[str],
        paths: list[list[str]],
    ) -> set[str]:
        allowed = set(linked_models)
        for path in paths:
            allowed.update(path)
        return allowed | (connected_models & allowed)

    def _relationship_paths(self, paths: list[list[str]]) -> list[RelationshipPath]:
        relationship_paths: list[RelationshipPath] = []
        for path in paths:
            relation_fields: dict[str, str] = {}
            for model, fields in self.traverser.relation_fields_for_path(path).items():
                if fields:
                    relation_fields[model] = sorted(fields)[0]
            relationship_paths.append(RelationshipPath(models=path, relation_fields=relation_fields))
        return relationship_paths

    def _confidence(self, candidates: list, linked_fields: dict[str, set[str]], paths: list[list[str]]) -> ConfidenceScores:
        retrieval_score = max((candidate.score for candidate in candidates), default=0.0)
        requested_field_count = sum(len(fields) for fields in linked_fields.values())
        linking_score = 1.0 if requested_field_count else 0.0
        graph_score = 1.0 if paths or len(linked_fields) <= 1 else 0.5
        final_score = (min(float(retrieval_score), 1.0) + linking_score + graph_score) / 3
        return ConfidenceScores(
            retrieval_score=round(float(retrieval_score), 4),
            linking_score=round(linking_score, 4),
            graph_score=round(graph_score, 4),
            final_score=round(final_score, 4),
        )
    def _ordered_models(self, anchor_model: str | None, selected_models: set[str], candidates: list) -> list[str]:
        ordered: list[str] = []
        if anchor_model in selected_models:
            ordered.append(anchor_model)
        for candidate in candidates:
            if candidate.model in selected_models and candidate.model not in ordered:
                ordered.append(candidate.model)
        for model_name in selected_models:
            if model_name not in ordered:
                ordered.append(model_name)
        return ordered

    def _validate(self, selected_fields: dict[str, set[str]]) -> tuple[dict[str, set[str]], int, int]:
        safe: dict[str, set[str]] = {}
        hallucinated_models = 0
        hallucinated_fields = 0

        for model_name, fields in selected_fields.items():
            model = self.schema.models.get(model_name)
            if not model:
                hallucinated_models += 1
                continue
            safe[model_name] = set()
            for field_name in fields:
                field = model.fields.get(field_name)
                if not field:
                    hallucinated_fields += 1
                    continue
                if field.relation and field.relation not in self.schema.models:
                    hallucinated_fields += 1
                    continue
                safe[model_name].add(field_name)

        return safe, hallucinated_models, hallucinated_fields
