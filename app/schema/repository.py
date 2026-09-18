import json
from hashlib import sha256
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
        return OrmMapper().map(self.load_raw())

    @property
    def metadata_path(self) -> Path:
        return self.orm_schema_path.with_suffix('.metadata.json')

    def _source_metadata(self) -> dict:
        schema_dir = Path(__file__).parent
        sources = [
            self.sql_path,
            schema_dir / 'orm_mapper.py',
            schema_dir / 'adapters' / 'postgres_sql_adapter.py',
            schema_dir / 'models.py',
            schema_dir / 'aliases.py',
            DEFAULT_ALIAS_PATH,
        ]
        return {
            'schema_source': str(self.sql_path.resolve()),
            'sources': {str(path.resolve()): sha256(path.read_bytes()).hexdigest() for path in sources},
        }

    def save_orm_schema(self, schema: OrmSchema) -> None:
        self.orm_schema_path.parent.mkdir(parents=True, exist_ok=True)
        payload = schema.model_dump_json(indent=2)
        self.orm_schema_path.write_text(payload, encoding='utf-8')
        metadata = self._source_metadata()
        metadata['artifact_sha256'] = sha256(self.orm_schema_path.read_bytes()).hexdigest()
        self.metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    def load_or_build_orm_schema(self) -> OrmSchema:
        if self._cache_is_fresh():
            payload = json.loads(self.orm_schema_path.read_text(encoding='utf-8'))
            return OrmSchema.model_validate(payload)
        schema = self.build_orm_schema()
        self.save_orm_schema(schema)
        return schema

    def _cache_is_fresh(self) -> bool:
        if not self.orm_schema_path.exists() or not self.metadata_path.exists():
            return False
        try:
            metadata = json.loads(self.metadata_path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return False
        if not isinstance(metadata, dict):
            return False
        expected = self._source_metadata()
        return (
            all(metadata.get(key) == value for key, value in expected.items())
            and metadata.get('artifact_sha256') == sha256(self.orm_schema_path.read_bytes()).hexdigest()
        )
