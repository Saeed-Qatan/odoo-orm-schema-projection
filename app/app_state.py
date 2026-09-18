import logging

from app.core.config import Settings, get_settings
from app.graph.builder import SchemaGraphBuilder
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.repository import SchemaRepository


def build_pipeline(settings: Settings | None = None) -> SchemaProjectionPipeline:
    settings = settings or get_settings()
    repository = SchemaRepository(settings.schema_sql_path, settings.orm_schema_path)
    schema = repository.load_or_build_orm_schema()
    pipeline = SchemaProjectionPipeline(schema, settings)
    try:
        SchemaGraphBuilder().save(pipeline.graph, settings.graph_path)
    except OSError as exc:
        logging.getLogger(__name__).warning("Could not save schema graph: %s", exc)
    return pipeline
