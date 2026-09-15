from app.core.config import get_settings
from app.graph.builder import SchemaGraphBuilder
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.repository import SchemaRepository


def build_pipeline() -> SchemaProjectionPipeline:
    settings = get_settings()
    repository = SchemaRepository(settings.schema_sql_path, settings.orm_schema_path)
    schema = repository.load_or_build_orm_schema()
    pipeline = SchemaProjectionPipeline(schema, settings)
    try:
        SchemaGraphBuilder().save(pipeline.graph, settings.graph_path)
    except OSError:
        pass
    return pipeline
