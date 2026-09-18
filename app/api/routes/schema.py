from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import Settings, get_settings
from app.core.rate_limit import InMemoryRateLimiter
from app.schema.models import OrmSchema


def create_schema_router(schema: OrmSchema, limiter: InMemoryRateLimiter, settings: Settings | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/v1/schema", tags=["schema"])

    def read_limit(request: Request) -> None:
        runtime_settings = settings or get_settings()
        limiter.check(request, runtime_settings.read_rate_limit_per_minute, "schema-read")

    @router.get("/models", dependencies=[Depends(read_limit)])
    def list_models() -> dict:
        return {"models": sorted(schema.models.keys())}

    @router.get("/models/{model_name}", dependencies=[Depends(read_limit)])
    def get_model(model_name: str) -> dict:
        model = schema.models.get(model_name)
        if model is None:
            raise HTTPException(status_code=404, detail="Model not found")
        return model.model_dump()

    return router
