import argparse
import json
from pathlib import Path

from app.schema.adapters.orm_metadata_json_adapter import OrmMetadataJsonAdapter
from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.models import OrmSchema, RawDatabaseSchema
from app.schema.orm_mapper import OrmMapper

SYNTHETIC_MARKERS = (
    "EXPANDED TEST FIXTURE",
    "NOT AN AUTHENTIC ODOO SALES EXPORT",
    "synthetic metadata",
)

SAMPLE_MARKERS = (
    '"kind": "sample"',
    '"authentic": false',
    "development. not an authentic odoo export",
)

CORE_MODELS = {
    "sale.order",
    "sale.order.line",
    "product.product",
    "res.partner",
    "res.users",
    "res.company",
    "res.currency",
}

SCALE_MODELS = {
    "account.move",
    "purchase.order",
    "stock.picking",
}

CORE_FIELDS = {
    "sale.order": {"partner_id", "date_order", "user_id", "company_id", "currency_id"},
    "sale.order.line": {"order_id", "product_id", "product_uom_qty"},
    "product.product": set(),
    "res.partner": {"name"},
    "res.users": {"partner_id"},
    "res.company": {"name"},
    "res.currency": {"name"},
}


def evaluate_schema_source(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".json":
        return _evaluate_metadata_source(path, text)
    return _evaluate_sql_source(path, text)


def _evaluate_sql_source(path: Path, sql: str) -> dict:
    synthetic_marker_found = any(marker.lower() in sql.lower() for marker in SYNTHETIC_MARKERS)
    raw = PostgresSqlSchemaAdapter().load(path)
    schema = OrmMapper().map(raw)
    report = _schema_readiness(path, schema, synthetic_marker_found, sample_marker_found=False)
    report.update({"source_kind": "postgres_sql", "table_count": len(raw.tables)})
    return report


def _evaluate_metadata_source(path: Path, text: str) -> dict:
    synthetic_marker_found = any(marker.lower() in text.lower() for marker in SYNTHETIC_MARKERS)
    sample_marker_found = any(marker.lower() in text.lower() for marker in SAMPLE_MARKERS)
    schema = OrmMetadataJsonAdapter().load(path)
    report = _schema_readiness(path, schema, synthetic_marker_found, sample_marker_found)
    report.update({"source_kind": "orm_metadata_json", "table_count": None, "module_count": len(schema.models)})
    return report


def _schema_readiness(
    path: Path,
    schema: OrmSchema,
    synthetic_marker_found: bool,
    sample_marker_found: bool,
) -> dict:
    model_names = set(schema.models)
    missing_core_models = sorted(CORE_MODELS - model_names)
    missing_scale_models = sorted(SCALE_MODELS - model_names)
    missing_core_fields: dict[str, list[str]] = {}
    for model_name, expected_fields in CORE_FIELDS.items():
        model = schema.models.get(model_name)
        if not model:
            if expected_fields:
                missing_core_fields[model_name] = sorted(expected_fields)
            continue
        missing = sorted(expected_fields - set(model.fields))
        if missing:
            missing_core_fields[model_name] = missing

    is_authentic_candidate = (
        not synthetic_marker_found
        and not sample_marker_found
        and not missing_core_models
        and not missing_core_fields
    )
    is_scale_ready = is_authentic_candidate and not missing_scale_models

    return {
        "path": str(path),
        "model_count": len(schema.models),
        "synthetic_marker_found": synthetic_marker_found,
        "sample_marker_found": sample_marker_found,
        "missing_core_models": missing_core_models,
        "missing_core_fields": missing_core_fields,
        "missing_scale_models": missing_scale_models,
        "is_authentic_candidate": is_authentic_candidate,
        "is_scale_ready": is_scale_ready,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect whether a schema source is ready for authentic Odoo scale testing.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate_schema_source(args.path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
