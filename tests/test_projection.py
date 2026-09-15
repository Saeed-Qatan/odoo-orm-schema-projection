from pathlib import Path

from app.core.config import Settings
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.models import ProjectionOptions
from app.schema.orm_mapper import OrmMapper


def test_projection_returns_minimal_schema_without_hallucination() -> None:
    raw = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))
    schema = OrmMapper().map(raw)
    pipeline = SchemaProjectionPipeline(schema, Settings(enable_dense_retrieval=False))

    result = pipeline.run(
        "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية",
        ProjectionOptions(debug=True),
    )

    assert "sale.order" in result.models
    assert result.debug is not None
    assert result.debug.metrics.hallucinated_models == 0
    assert result.debug.metrics.hallucinated_fields == 0
    assert result.debug.metrics.latency_ms <= 1500
    assert "sale.order" in result.schema_
    sale_order_fields = result.schema_["sale.order"]["fields"]
    assert "date_order" in sale_order_fields
    assert "partner_id" in sale_order_fields
    assert "sale_order_line_ids" in sale_order_fields
    line_fields = sale_order_fields["sale_order_line_ids"]["fields"]
    assert "product_uom_qty" in line_fields
    assert "product_id" in line_fields
    assert "name" in sale_order_fields["partner_id"]["fields"]
    assert "name" in line_fields["product_id"]["fields"]

