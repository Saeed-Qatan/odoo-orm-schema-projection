from pathlib import Path

from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.orm_mapper import OrmMapper


def test_orm_mapper_converts_tables_and_relations() -> None:
    raw = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))
    schema = OrmMapper().map(raw)

    assert "sale.order" in schema.models
    assert schema.models["sale.order"].fields["partner_id"].type == "many2one"
    assert schema.models["sale.order"].fields["partner_id"].relation == "res.partner"
    assert schema.models["res.partner"].fields["sale_order_ids"].type == "one2many"
    assert schema.models["res.partner"].fields["sale_order_ids"].inferred is True

def test_orm_mapper_reverse_relation_name_is_synthetic_and_documented() -> None:
    raw = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))
    schema = OrmMapper().map(raw)

    field = schema.models["sale.order"].fields["sale_order_line_ids"]
    assert field.type == "one2many"
    assert field.relation == "sale.order.line"
    assert field.inverse == "order_id"
    assert field.inferred is True
