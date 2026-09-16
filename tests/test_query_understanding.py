from app.projection.query_understanding import QueryUnderstandingExtractor
from app.schema.aliases import get_alias_catalog


def test_alias_catalog_loads_from_json() -> None:
    aliases = get_alias_catalog()

    assert "sale.order" in aliases.model_aliases
    assert "partner_id" in aliases.field_aliases
    assert "customer" in aliases.entities


def test_query_understanding_extracts_sales_filters_and_fields() -> None:
    understanding = QueryUnderstandingExtractor().understand(
        "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية"
    )

    assert understanding.intent == "sales_analysis"
    assert set(understanding.entities) == {"sales", "customer", "product", "quantity", "date"}
    assert understanding.filters == {"month": "august", "salesperson": "أحمد"}
    assert understanding.anchor_model == "sale.order"
    assert understanding.required_fields["sale.order"] == ["partner_id", "date_order", "user_id"]
    assert understanding.required_fields["sale.order.line"] == ["product_id", "product_uom_qty"]
    assert understanding.required_fields["product.product"] == ["name"]


def test_query_understanding_supports_total_and_status() -> None:
    understanding = QueryUnderstandingExtractor().understand("اعرض حالة الطلب وإجمالي المبيعات")

    assert understanding.intent == "sales_analysis"
    assert set(understanding.entities) == {"sales", "total", "status"}
    assert understanding.required_fields["sale.order"] == ["amount_total", "state"]
