import json
from pathlib import Path

from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.models import OrmSchema, RawDatabaseSchema
from app.schema.aliases import DEFAULT_ALIAS_PATH
from app.schema.orm_mapper import OrmMapper


class SchemaRepository:
    def __init__(self, sql_path: Path, orm_schema_path: Path) -> None:
        self.sql_path = sql_path
        self.orm_schema_path = orm_schema_path

    def load_raw(self) -> RawDatabaseSchema:
        return PostgresSqlSchemaAdapter().load(self.sql_path)

    def build_orm_schema(self) -> OrmSchema:
        raw = self.load_raw()
        return OrmMapper().map(raw)

    def save_orm_schema(self, schema: OrmSchema) -> None:
        self.orm_schema_path.parent.mkdir(parents=True, exist_ok=True)
        self.orm_schema_path.write_text(schema.model_dump_json(indent=2), encoding="utf-8")

    def load_or_build_orm_schema(self) -> OrmSchema:
        if self._cache_is_fresh():
            payload = json.loads(self.orm_schema_path.read_text(encoding="utf-8"))
            return OrmSchema.model_validate(payload)
        schema = self.build_orm_schema()
        self.save_orm_schema(schema)
        return schema

    def _cache_is_fresh(self) -> bool:
        if not self.orm_schema_path.exists():
            return False
        cache_mtime = self.orm_schema_path.stat().st_mtime
        source_paths = [self.sql_path, Path(__file__).with_name("orm_mapper.py"), DEFAULT_ALIAS_PATH]
        return all(cache_mtime >= source.stat().st_mtime for source in source_paths if source.exists())


