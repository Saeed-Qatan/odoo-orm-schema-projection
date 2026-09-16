from statistics import median
from typing import Any

from app.schema.models import OrmSchema, ProjectionResponse


def precision_recall(expected: set[str], actual: set[str]) -> tuple[float, float]:
    if not actual:
        return 0.0, 0.0
    true_positive = len(expected & actual)
    precision = true_positive / len(actual) if actual else 0.0
    recall = true_positive / len(expected) if expected else 1.0
    return precision, recall


def collect_projected_fields(projected_schema: dict) -> set[str]:
    actual_fields: set[str] = set()

    def visit(model_name: str, fields: dict[str, Any]) -> None:
        for field_name, payload in fields.items():
            actual_fields.add(f"{model_name}.{field_name}")
            relation = payload.get("relation") if isinstance(payload, dict) else None
            child_fields = payload.get("fields") if isinstance(payload, dict) else None
            if relation and isinstance(child_fields, dict):
                visit(relation, child_fields)

    for root_model, model_payload in projected_schema.items():
        visit(root_model, model_payload.get("fields", {}))
    return actual_fields


def relationship_validity(result: ProjectionResponse, schema: OrmSchema | None = None) -> float:
    if schema is None:
        return 1.0 if result.debug and result.debug.metrics.hallucinated_models == 0 and result.debug.metrics.hallucinated_fields == 0 else 0.0

    valid = True

    def visit(model_name: str, fields: dict[str, Any]) -> None:
        nonlocal valid
        model = schema.models.get(model_name)
        if not model:
            valid = False
            return
        for field_name, payload in fields.items():
            field = model.fields.get(field_name)
            if not field:
                valid = False
                continue
            relation = payload.get("relation") if isinstance(payload, dict) else None
            child_fields = payload.get("fields") if isinstance(payload, dict) else None
            if relation:
                if field.relation != relation or relation not in schema.models:
                    valid = False
                if isinstance(child_fields, dict):
                    visit(relation, child_fields)

    for root_model, model_payload in result.schema_.items():
        visit(root_model, model_payload.get("fields", {}))
    return 1.0 if valid else 0.0


def evaluate_projection(
    result: ProjectionResponse,
    expected_models: list[str],
    expected_fields: dict[str, list[str]],
    expected_paths: list[list[str]] | None = None,
    max_extra_fields: int | None = None,
    schema: OrmSchema | None = None,
) -> dict:
    actual_models = set(result.models)
    expected_model_set = set(expected_models)
    model_precision, model_recall = precision_recall(expected_model_set, actual_models)

    actual_fields = collect_projected_fields(result.schema_)
    expected_field_set = {
        f"{model_name}.{field_name}"
        for model_name, fields in expected_fields.items()
        for field_name in fields
    }
    field_precision, field_recall = precision_recall(expected_field_set, actual_fields)

    actual_paths = result.debug.paths if result.debug else []
    expected_paths = expected_paths or []
    missing_paths = [path for path in expected_paths if path not in actual_paths]
    extra_fields = actual_fields - expected_field_set
    over_selection_count = len(extra_fields)
    over_selection_ok = True if max_extra_fields is None else over_selection_count <= max_extra_fields

    latency_ms = result.debug.metrics.latency_ms if result.debug else 0
    hallucinated_models = result.debug.metrics.hallucinated_models if result.debug else 0
    hallucinated_fields = result.debug.metrics.hallucinated_fields if result.debug else 0
    reduction_ratio = result.debug.metrics.reduction_ratio if result.debug else 0

    return {
        "model_precision": model_precision,
        "model_recall": model_recall,
        "field_precision": field_precision,
        "field_recall": field_recall,
        "relationship_validity": relationship_validity(result, schema),
        "reduction_ratio": reduction_ratio,
        "latency_ms": latency_ms,
        "hallucinated_models": hallucinated_models,
        "hallucinated_fields": hallucinated_fields,
        "hallucination_count": hallucinated_models + hallucinated_fields,
        "over_selection_count": over_selection_count,
        "over_selection_ok": over_selection_ok,
        "missing_paths": missing_paths,
    }


def summarize(results: list[dict]) -> dict:
    latencies = [item["latency_ms"] for item in results]
    sorted_latencies = sorted(latencies)
    p95_index = max(0, int(len(sorted_latencies) * 0.95) - 1)
    return {
        "count": len(results),
        "model_precision_avg": sum(item["model_precision"] for item in results) / len(results),
        "model_recall_avg": sum(item["model_recall"] for item in results) / len(results),
        "field_precision_avg": sum(item["field_precision"] for item in results) / len(results),
        "field_recall_avg": sum(item["field_recall"] for item in results) / len(results),
        "relationship_validity_avg": sum(item["relationship_validity"] for item in results) / len(results),
        "reduction_ratio_avg": sum(item["reduction_ratio"] for item in results) / len(results),
        "latency_p50_ms": median(latencies),
        "latency_p95_ms": sorted_latencies[p95_index],
        "hallucination_count": sum(item["hallucination_count"] for item in results),
        "over_selection_count": sum(item["over_selection_count"] for item in results),
        "failed_path_count": sum(len(item["missing_paths"]) for item in results),
    }
