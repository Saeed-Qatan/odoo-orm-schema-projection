from pathlib import Path

from app.core.config import Settings
from app.evaluation.metadata_golden_set import METADATA_GOLDEN_SET
from app.evaluation.runner import build_metadata_pipeline, run_evaluation
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.adapters.orm_metadata_json_adapter import OrmMetadataJsonAdapter
from app.schema.models import ProjectionOptions


SAMPLE_PATH = Path("data/raw/odoo/orm_metadata.sample.json")


def test_metadata_pipeline_projects_existing_api_shape() -> None:
    schema = OrmMetadataJsonAdapter().load(SAMPLE_PATH)
    pipeline = SchemaProjectionPipeline(schema, Settings(enable_dense_retrieval=False))

    result = pipeline.run("أعطني المبيعات مع اسم العميل وبلد العميل واسم المندو", ProjectionOptions(debug=True))

    assert result.supported is True
    assert "sale.order" in result.models
    assert "res.company" not in result.models
    fields = result.schema_["sale.order"]["fields"]
    assert set(fields) == {"partner_id", "user_id"}
    assert set(fields["partner_id"]["fields"]) == {"name", "country_id"}
    assert set(fields["user_id"]["fields"]["partner_id"]["fields"]) == {"name"}
    assert result.debug is not None
    assert result.debug.metrics.hallucinated_models == 0
    assert result.debug.metrics.hallucinated_fields == 0


def test_metadata_evaluation_report_has_zero_hallucination(tmp_path: Path) -> None:
    pipeline = build_metadata_pipeline(SAMPLE_PATH)
    report = run_evaluation(pipeline, METADATA_GOLDEN_SET, tmp_path / "metadata_report.json")

    assert report["summary"]["count"] == len(METADATA_GOLDEN_SET)
    assert report["summary"]["hallucination_count"] == 0
    assert report["summary"]["relationship_validity_avg"] == 1.0
    assert (tmp_path / "metadata_report.json").exists()
