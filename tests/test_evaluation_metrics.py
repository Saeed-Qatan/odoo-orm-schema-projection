from pathlib import Path

from app.core.config import Settings
from app.evaluation.metrics import collect_projected_fields, evaluate_projection
from app.evaluation.runner import run_evaluation
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.models import ProjectionOptions
from app.schema.orm_mapper import OrmMapper


def build_pipeline() -> SchemaProjectionPipeline:
    raw = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))
    schema = OrmMapper().map(raw)
    return SchemaProjectionPipeline(schema, Settings(enable_dense_retrieval=False))


def test_collect_projected_fields_includes_nested_relation_fields() -> None:
    pipeline = build_pipeline()
    result = pipeline.run(
        "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية",
        ProjectionOptions(debug=True),
    )

    fields = collect_projected_fields(result.schema_)

    assert "sale.order.partner_id" in fields
    assert "res.partner.name" in fields
    assert "sale.order.line.product_id" in fields
    assert "product.product.name" in fields


def test_evaluate_projection_reports_nested_precision_and_valid_relationships() -> None:
    pipeline = build_pipeline()
    result = pipeline.run("أعطني المبيعات مع اسم المنتج والكمية", ProjectionOptions(debug=True))

    metrics = evaluate_projection(
        result,
        expected_models=["sale.order", "sale.order.line", "product.product"],
        expected_fields={
            "sale.order": ["sale_order_line_ids"],
            "sale.order.line": ["product_id", "product_uom_qty"],
            "product.product": ["name"],
        },
        expected_paths=[["sale.order", "sale.order.line"], ["sale.order", "sale.order.line", "product.product"]],
        max_extra_fields=0,
        schema=pipeline.schema,
    )

    assert metrics["field_precision"] == 1.0
    assert metrics["field_recall"] == 1.0
    assert metrics["relationship_validity"] == 1.0
    assert metrics["over_selection_count"] == 0


def test_run_evaluation_writes_report(tmp_path: Path) -> None:
    pipeline = build_pipeline()
    output_path = tmp_path / "evaluation_report.json"

    report = run_evaluation(
        pipeline=pipeline,
        golden_set=[
            {
                "query": "أعطني مبيعات أحمد فقط",
                "expected_models": ["sale.order"],
                "expected_fields": {"sale.order": ["user_id"]},
                "expected_paths": [],
                "max_extra_fields": 0,
            }
        ],
        output_path=output_path,
    )

    assert output_path.exists()
    assert report["summary"]["count"] == 1
    assert report["summary"]["hallucination_count"] == 0
