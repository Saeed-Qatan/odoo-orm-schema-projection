from pathlib import Path

from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter


def test_postgres_adapter_extracts_tables_columns_and_foreign_keys() -> None:
    schema = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))

    assert "sale_order" in schema.tables
    assert any(column.name == "partner_id" for column in schema.tables["sale_order"].columns)
    assert any(fk.table == "sale_order" and fk.ref_table == "res_partner" for fk in schema.foreign_keys)
