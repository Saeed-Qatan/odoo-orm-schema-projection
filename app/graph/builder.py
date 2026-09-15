import json
from pathlib import Path

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None

from app.schema.models import OrmSchema


class SchemaGraphBuilder:
    def build(self, schema: OrmSchema):
        if nx is None:
            raise RuntimeError("networkx is required to build the schema graph")

        graph = nx.MultiDiGraph()
        for model in schema.models.values():
            model_node = f"model:{model.name}"
            graph.add_node(model_node, kind="model", model=model.name)
            for field in model.fields.values():
                field_node = f"field:{model.name}.{field.name}"
                graph.add_node(
                    field_node,
                    kind="field",
                    model=model.name,
                    field=field.name,
                    field_type=field.type,
                    relation=field.relation,
                    inferred=field.inferred,
                )
                graph.add_edge(model_node, field_node, kind="contains", field=field.name)
                graph.add_edge(field_node, model_node, kind="belongs_to")
                if field.relation and field.relation in schema.models:
                    target_node = f"model:{field.relation}"
                    graph.add_edge(
                        field_node,
                        target_node,
                        kind="relation",
                        relation_type=field.type,
                        field=field.name,
                        inferred=field.inferred,
                    )
                    graph.add_edge(
                        model_node,
                        target_node,
                        kind="model_relation",
                        relation_type=field.type,
                        field=field.name,
                        inferred=field.inferred,
                    )
        return graph

    def save(self, graph, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": [{"id": node, **data} for node, data in graph.nodes(data=True)],
            "edges": [{"source": src, "target": dst, **data} for src, dst, data in graph.edges(data=True)],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, path: Path):
        if nx is None:
            raise RuntimeError("networkx is required to load the schema graph")
        payload = json.loads(path.read_text(encoding="utf-8"))
        graph = nx.MultiDiGraph()
        for node in payload.get("nodes", []):
            node = dict(node)
            node_id = node.pop("id")
            graph.add_node(node_id, **node)
        for edge in payload.get("edges", []):
            edge = dict(edge)
            source = edge.pop("source")
            target = edge.pop("target")
            graph.add_edge(source, target, **edge)
        return graph
