from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Odoo ORM Schema Projection"
    debug: bool = False

    schema_sql_path: Path = Path("data/raw/odoo/schema.sql")
    orm_schema_path: Path = Path("data/processed/odoo_orm_schema.json")
    graph_path: Path = Path("data/processed/odoo_schema_graph.json")
    index_dir: Path = Path("data/indexes")

    enable_dense_retrieval: bool = False
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    project_schema_rate_limit_per_minute: int = Field(default=30, ge=1)
    read_rate_limit_per_minute: int = Field(default=100, ge=1)
    request_timeout_ms: int = Field(default=1500, ge=100)

    max_query_length: int = Field(default=500, ge=20)
    default_max_models: int = Field(default=5, ge=1)
    default_max_depth: int = Field(default=3, ge=1)
    default_max_fields_per_model: int = Field(default=8, ge=1)
    default_max_total_fields: int = Field(default=30, ge=1)
    top_k_bm25: int = Field(default=30, ge=1)
    top_k_dense: int = Field(default=30, ge=1)
    top_k_final: int = Field(default=20, ge=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
