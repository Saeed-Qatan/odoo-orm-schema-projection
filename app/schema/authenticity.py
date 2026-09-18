import argparse
import json
from pathlib import Path

from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.orm_mapper import OrmMapper

SYNTHETIC_MARKERS = (
    "EXPANDED TEST FIXTURE",
    "NOT AN AUTHENTIC ODOO SALES EXPORT",
    "synthetic metadata",
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
    sql = path.read_text(encoding="utf-8", errors="ignore")
    synthetic_marker_found = any(marker.lower() in sql.lower() for marker in SYNTHETIC_MARKERS)
    raw = PostgresSqlSchemaAdapter().load(path)
    schema = OrmMapper().map(raw)

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

    is_authentic_candidate = not synthetic_marker_found and not missing_core_models and not missing_core_fields
    is_scale_ready = is_authentic_candidate and not missing_scale_models

    return {
        "path": str(path),
        "table_count": len(raw.tables),
        "model_count": len(schema.models),
        "synthetic_marker_found": synthetic_marker_found,
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