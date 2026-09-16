from pathlib import Path

from app.core.config import Settings
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.models import ProjectionOptions
from app.schema.orm_mapper import OrmMapper


QUERY = "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية"


def build_pipeline() -> SchemaProjectionPipeline:
    raw = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))
    schema = OrmMapper().map(raw)
    return SchemaProjectionPipeline(schema, Settings(enable_dense_retrieval=False))


def test_projection_returns_query_guided_minimal_schema_without_hallucination() -> None:
    pipeline = build_pipeline()

    result = pipeline.run(QUERY, ProjectionOptions(debug=True))

    assert result.models == ["sale.order", "sale.order.line", "res.partner", "product.product"]
    assert result.debug is not None
    assert result.debug.metrics.hallucinated_models == 0
    assert result.debug.metrics.hallucinated_fields == 0
    assert result.debug.metrics.latency_ms <= 1500

    assert result.debug.query_understanding is not None
    assert result.debug.query_understanding.intent == "sales_analysis"
    assert set(result.debug.query_understanding.entities) == {"sales", "customer", "product", "quantity", "date"}
    assert result.debug.query_understanding.filters == {"month": "august", "salesperson": "أحمد"}
    assert result.debug.query_understanding.anchor_model == "sale.order"

    assert result.debug.paths == [
        ["sale.order", "res.partner"],
        ["sale.order", "sale.order.line"],
        ["sale.order", "sale.order.line", "product.product"],
    ]

    assert "sale.order" in result.schema_
    sale_order_fields = result.schema_["sale.order"]["fields"]
    assert set(sale_order_fields) == {"date_order", "partner_id", "sale_order_line_ids", "user_id"}

    partner_fields = sale_order_fields["partner_id"]["fields"]
    assert set(partner_fields) == {"name"}

    line_fields = sale_order_fields["sale_order_line_ids"]["fields"]
    assert set(line_fields) == {"product_id", "product_uom_qty"}

    product_fields = line_fields["product_id"]["fields"]
    assert set(product_fields) == {"name"}

    assert "res.country" not in result.models
    assert "res.company" not in result.models
