import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import projection as projection_routes
from app.api.routes import schema as schema_routes
from app.api.routes.projection import create_projection_router
from app.api.routes.schema import create_schema_router
from app.core.config import Settings
from app.core.rate_limit import InMemoryRateLimiter
from app.main import app
from app.schema.models import OrmSchema, ProjectionResponse


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


def test_project_schema_rejects_query_longer_than_limit() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/project-schema",
        json={"query": "x" * 501, "options": {}},
    )

    assert response.status_code == 422


def test_project_schema_rate_limit_returns_429(monkeypatch) -> None:
    test_app = FastAPI()
    monkeypatch.setattr(
        projection_routes,
        "get_settings",
        lambda: Settings(project_schema_rate_limit_per_minute=1),
    )
    test_app.include_router(create_projection_router(_FastPipeline(), InMemoryRateLimiter()))
    client = TestClient(test_app)

    first = client.post("/api/v1/project-schema", json={"query": "أعطني اسم العميل", "options": {}})
    second = client.post("/api/v1/project-schema", json={"query": "أعطني اسم العميل", "options": {}})

    assert first.status_code == 200
    assert second.status_code == 429


def test_schema_read_rate_limit_returns_429(monkeypatch) -> None:
    test_app = FastAPI()
    monkeypatch.setattr(
        schema_routes,
        "get_settings",
        lambda: Settings(read_rate_limit_per_minute=1),
    )
    test_app.include_router(create_schema_router(OrmSchema(), InMemoryRateLimiter()))
    client = TestClient(test_app)

    first = client.get("/api/v1/schema/models")
    second = client.get("/api/v1/schema/models")

    assert first.status_code == 200
    assert second.status_code == 429


def test_project_schema_timeout_returns_504(monkeypatch) -> None:
    test_app = FastAPI()
    monkeypatch.setattr(
        projection_routes,
        "get_settings",
        lambda: Settings(project_schema_rate_limit_per_minute=100, request_timeout_ms=100),
    )
    test_app.include_router(create_projection_router(_SlowPipeline(), InMemoryRateLimiter()))
    client = TestClient(test_app)

    response = client.post("/api/v1/project-schema", json={"query": "أعطني اسم العميل", "options": {}})

    assert response.status_code == 504


class _FastPipeline:
    def run(self, query, options) -> ProjectionResponse:
        return ProjectionResponse(query=query, models=[], schema={})


class _SlowPipeline:
    def run(self, query, options) -> ProjectionResponse:
        time.sleep(0.2)
        return ProjectionResponse(query=query, models=[], schema={})
