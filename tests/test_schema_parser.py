from pathlib import Path

from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter


def test_postgres_adapter_extracts_tables_columns_and_foreign_keys() -> None:
    schema = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))

    assert "sale_order" in schema.tables
    assert any(column.name == "partner_id" for column in schema.tables["sale_order"].columns)
    assert any(fk.table == "sale_order" and fk.ref_table == "res_partner" for fk in schema.foreign_keys)

from pathlib import Path

from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter


def test_parser_handles_inline_and_alter_table_foreign_keys(tmp_path: Path) -> None:
    sql = """
    CREATE TABLE res_partner (
        id integer PRIMARY KEY,
        name character varying NOT NULL
    );

    CREATE TABLE sale_order (
        id integer PRIMARY KEY,
        partner_id integer NOT NULL,
        CONSTRAINT sale_order_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES res_partner(id)
    );

    CREATE TABLE sale_order_line (
        id integer PRIMARY KEY,
        order_id integer NOT NULL
    );

    ALTER TABLE ONLY sale_order_line
        ADD CONSTRAINT sale_order_line_order_id_fkey FOREIGN KEY (order_id) REFERENCES sale_order(id);
    """
    path = tmp_path / "schema.sql"
    path.write_text(sql, encoding="utf-8")

    raw = PostgresSqlSchemaAdapter().load(path)

    assert set(raw.tables) == {"res_partner", "sale_order", "sale_order_line"}
    assert len(raw.foreign_keys) == 2
    assert {(fk.table, fk.column, fk.ref_table) for fk in raw.foreign_keys} == {
        ("sale_order", "partner_id", "res_partner"),
        ("sale_order_line", "order_id", "sale_order"),
    }
