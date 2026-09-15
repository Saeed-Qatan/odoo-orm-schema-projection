from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_project_schema_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/project-schema",
        json={
            "query": "أعطني اسم العميل والكمية",
            "options": {"debug": True},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["debug"]["metrics"]["hallucinated_models"] == 0
    assert payload["debug"]["metrics"]["latency_ms"] <= 1500
