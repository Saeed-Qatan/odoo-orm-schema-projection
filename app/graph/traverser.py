from collections import deque

from app.schema.models import OrmSchema


class GraphTraverser:
    def __init__(self, graph, schema: OrmSchema) -> None:
        self.graph = graph
        self.schema = schema

    def shortest_model_path(self, source_model: str, target_model: str) -> list[str]:
        if source_model == target_model:
            return [source_model]
        try:
            import networkx as nx

            nodes = nx.shortest_path(self.graph, f"model:{source_model}", f"model:{target_model}")
        except Exception:
            return []
        return [node.replace("model:", "") for node in nodes if node.startswith("model:")]

    def relation_fields_for_path(self, path: list[str]) -> dict[str, set[str]]:
        fields: dict[str, set[str]] = {}
        for current, nxt in zip(path, path[1:]):
            model = self.schema.models.get(current)
            if not model:
                continue
            for field in model.fields.values():
                if field.relation == nxt:
                    fields.setdefault(current, set()).add(field.name)
                    break
        return fields

    def bfs_models(self, seed_models: set[str], max_depth: int) -> set[str]:
        selected = set(seed_models)
        queue = deque((model, 0) for model in seed_models)
        while queue:
            model_name, depth = queue.popleft()
            if depth >= max_depth:
                continue
            model = self.schema.models.get(model_name)
            if not model:
                continue
            for field in model.fields.values():
                if not field.relation or field.relation in selected:
                    continue
                selected.add(field.relation)
                queue.append((field.relation, depth + 1))
        return selected

    def connect_models(self, seed_models: set[str], max_depth: int) -> tuple[set[str], dict[str, set[str]], list[list[str]]]:
        selected = set(seed_models)
        relation_fields: dict[str, set[str]] = {}
        paths: list[list[str]] = []
        seeds = list(seed_models)

        for idx, source in enumerate(seeds):
            for target in seeds[idx + 1 :]:
                path = self.shortest_model_path(source, target)
                if not path or len(path) - 1 > max_depth:
                    continue
                paths.append(path)
                selected.update(path)
                for model, fields in self.relation_fields_for_path(path).items():
                    relation_fields.setdefault(model, set()).update(fields)

        return selected, relation_fields, paths
