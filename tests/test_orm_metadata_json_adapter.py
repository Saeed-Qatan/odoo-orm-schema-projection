from pathlib import Path

from app.schema.adapters.orm_metadata_json_adapter import OrmMetadataJsonAdapter


SAMPLE_PATH = Path("data/raw/odoo/orm_metadata.sample.json")


def test_metadata_json_adapter_preserves_model_and_field_metadata() -> None:
    schema = OrmMetadataJsonAdapter().load(SAMPLE_PATH)

    sale_order = schema.models["sale.order"]
    assert sale_order.table == "sale_order"
    assert sale_order.category == "Sales"
    assert sale_order.common_domains[0]["name"] == "confirmed"
    assert "commercial" in sale_order.field_groups
    assert sale_order.fields["state"].choices[0] == ["draft", "Quotation"]
    assert sale_order.fields["partner_id"].relation == "res.partner"


def test_metadata_json_adapter_infers_reverse_one2many_relations() -> None:
    schema = OrmMetadataJsonAdapter().load(SAMPLE_PATH)

    sale_order = schema.models["sale.order"]
    assert "sale_order_line_ids" in sale_order.fields
    reverse = sale_order.fields["sale_order_line_ids"]
    assert reverse.type == "one2many"
    assert reverse.relation == "sale.order.line"
    assert reverse.inverse == "order_id"
    assert reverse.inferred is True


def test_metadata_json_adapter_keeps_relationships_projectable() -> None:
    schema = OrmMetadataJsonAdapter().load(SAMPLE_PATH)

    assert schema.models["sale.order"].fields["user_id"].relation == "res.users"
    assert schema.models["res.users"].fields["partner_id"].relation == "res.partner"
    assert schema.models["product.product"].fields["product_tmpl_id"].relation == "product.template"
