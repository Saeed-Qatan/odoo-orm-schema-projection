from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.projection import create_projection_router
from app.api.routes.schema import create_schema_router
from app.app_state import build_pipeline
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import InMemoryRateLimiter

configure_logging()
settings = get_settings()
pipeline = build_pipeline()
limiter = InMemoryRateLimiter()

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(health_router)
app.include_router(create_schema_router(pipeline.schema, limiter))
app.include_router(create_projection_router(pipeline, limiter))


@app.get("/")
def root() -> dict:
    return {"message": settings.app_name, "status": "running"}
