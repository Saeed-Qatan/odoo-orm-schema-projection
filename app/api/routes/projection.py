import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import get_settings
from app.core.rate_limit import InMemoryRateLimiter
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.models import ProjectionRequest, ProjectionResponse


def create_projection_router(pipeline: SchemaProjectionPipeline, limiter: InMemoryRateLimiter) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["projection"])

    def project_limit(request: Request) -> None:
        settings = get_settings()
        limiter.check(request, settings.project_schema_rate_limit_per_minute, "project-schema")

    @router.post("/project-schema", response_model=ProjectionResponse, dependencies=[Depends(project_limit)])
    async def project_schema(payload: ProjectionRequest) -> ProjectionResponse:
        settings = get_settings()
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(pipeline.run, payload.query, payload.options),
                timeout=settings.request_timeout_ms / 1000,
            )
        except (TimeoutError, asyncio.TimeoutError):
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Schema projection exceeded the request timeout.",
            ) from None

    return router

