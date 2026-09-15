from pathlib import Path

from app.graph.builder import SchemaGraphBuilder
from app.graph.traverser import GraphTraverser
from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.orm_mapper import OrmMapper


def test_graph_finds_sales_to_product_path() -> None:
    raw = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))
    schema = OrmMapper().map(raw)
    graph = SchemaGraphBuilder().build(schema)
    traverser = GraphTraverser(graph, schema)

    path = traverser.shortest_model_path("sale.order", "product.product")

    assert path == ["sale.order", "sale.order.line", "product.product"]
