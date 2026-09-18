"""Opt-in API runtime for the synthetic expanded schema fixture."""
from pathlib import Path

from app.application import create_app
from app.core.config import get_settings

settings = get_settings().model_copy(update={
    'schema_sql_path': Path('data/raw/odoo/schema.expanded.sql'),
    'orm_schema_path': Path('data/processed/odoo_orm_schema.expanded.json'),
    'graph_path': Path('data/processed/odoo_schema_graph.expanded.json'),
    'index_dir': Path('data/indexes/expanded'),
})
app = create_app(settings)
