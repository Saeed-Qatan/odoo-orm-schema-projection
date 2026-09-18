import argparse
import json
from pathlib import Path

from app.core.config import Settings
from app.evaluation.golden_set import GOLDEN_SET
from app.evaluation.metrics import evaluate_projection, summarize
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.models import ProjectionOptions
from app.schema.repository import SchemaRepository


DEFAULT_REPORT_PATH = Path("data/processed/evaluation_report.json")


def build_default_pipeline(settings: Settings | None = None) -> SchemaProjectionPipeline:
    settings = settings or Settings(enable_dense_retrieval=False)
    repository = SchemaRepository(settings.schema_sql_path, settings.orm_schema_path)
    schema = repository.load_or_build_orm_schema()
    return SchemaProjectionPipeline(schema, settings)


def run_evaluation(
    pipeline: SchemaProjectionPipeline | None = None,
    golden_set: list[dict] | None = None,
    output_path: Path | None = DEFAULT_REPORT_PATH,
) -> dict:
    pipeline = pipeline or build_default_pipeline()
    golden_set = golden_set or GOLDEN_SET
    cases: list[dict] = []

    for item in golden_set:
        options = ProjectionOptions.model_validate({**item.get("options", {}), "debug": True})
        result = pipeline.run(item["query"], options)
        metrics = evaluate_projection(
            result,
            expected_models=item["expected_models"],
            expected_fields=item["expected_fields"],
            expected_paths=item.get("expected_paths"),
            max_extra_fields=item.get("max_extra_fields"),
            schema=pipeline.schema,
        )
        cases.append({"query": item["query"], "models": result.models, "metrics": metrics})

    report = {"summary": summarize([case["metrics"] for case in cases]), "cases": cases}
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate schema projection fixtures")
    parser.add_argument("--expanded", action="store_true", help="Evaluate the synthetic expanded fixture")
    args = parser.parse_args()
    if args.expanded:
        from app.evaluation.expanded_golden_set import EXPANDED_GOLDEN_SET

        settings = Settings(
            schema_sql_path=Path("data/raw/odoo/schema.expanded.sql"),
            orm_schema_path=Path("data/processed/odoo_orm_schema.expanded.json"),
            enable_dense_retrieval=False,
        )
        repository = SchemaRepository(settings.schema_sql_path, settings.orm_schema_path)
        pipeline = SchemaProjectionPipeline(repository.build_orm_schema(), settings)
        report = run_evaluation(
            pipeline, EXPANDED_GOLDEN_SET, Path("data/processed/evaluation_report.expanded.json")
        )
    else:
        report = run_evaluation()
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
