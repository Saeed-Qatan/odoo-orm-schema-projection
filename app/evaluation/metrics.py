from statistics import median

from app.schema.models import ProjectionResponse


def precision_recall(expected: set[str], actual: set[str]) -> tuple[float, float]:
    if not actual:
        return 0.0, 0.0
    true_positive = len(expected & actual)
    precision = true_positive / len(actual) if actual else 0.0
    recall = true_positive / len(expected) if expected else 1.0
    return precision, recall


def evaluate_projection(result: ProjectionResponse, expected_models: list[str], expected_fields: dict[str, list[str]]) -> dict:
    actual_models = set(result.models)
    model_precision, model_recall = precision_recall(set(expected_models), actual_models)

    actual_fields = set()
    for model_name, model_payload in result.schema_.items():
        for field_name in model_payload.get("fields", {}):
            actual_fields.add(f"{model_name}.{field_name}")

    expected_field_set = {
        f"{model_name}.{field_name}"
        for model_name, fields in expected_fields.items()
        for field_name in fields
    }
    field_precision, field_recall = precision_recall(expected_field_set, actual_fields)

    latency_ms = result.debug.metrics.latency_ms if result.debug else 0
    hallucinated_models = result.debug.metrics.hallucinated_models if result.debug else 0
    hallucinated_fields = result.debug.metrics.hallucinated_fields if result.debug else 0

    return {
        "model_precision": model_precision,
        "model_recall": model_recall,
        "field_precision": field_precision,
        "field_recall": field_recall,
        "latency_ms": latency_ms,
        "hallucinated_models": hallucinated_models,
        "hallucinated_fields": hallucinated_fields,
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
        "latency_p50_ms": median(latencies),
        "latency_p95_ms": sorted_latencies[p95_index],
        "hallucination_count": sum(item["hallucinated_models"] + item["hallucinated_fields"] for item in results),
    }
