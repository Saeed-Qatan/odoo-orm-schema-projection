from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.projection import create_projection_router
from app.api.routes.schema import create_schema_router
from app.app_state import build_pipeline
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import InMemoryRateLimiter


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    settings = settings or get_settings()
    pipeline = build_pipeline(settings)
    limiter = InMemoryRateLimiter()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.state.settings = settings
    app.state.pipeline = pipeline
    app.include_router(health_router)
    app.include_router(create_schema_router(pipeline.schema, limiter, settings))
    app.include_router(create_projection_router(pipeline, limiter, settings))

    @app.get('/')
    def root() -> dict:
        return {'message': settings.app_name, 'status': 'running'}

    return app
