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


def test_query_understanding_matches_arabic_typo_with_debug_term() -> None:
    understanding = QueryUnderstandingExtractor().understand(
        "أعطني المبيعات مع اسم العميل وبلد العميل واسم المندو"
    )

    assert "salesperson_name" in understanding.entities
    assert any(
        term.input == "المندو"
        and term.matched == "المندوب"
        and term.target == "salesperson_name"
        for term in understanding.matched_terms
    )


def test_query_understanding_marks_general_question_as_out_of_domain() -> None:
    understanding = QueryUnderstandingExtractor().understand("ماهي تكنولوجيا المعلومات")

    assert understanding.intent is None
    assert understanding.entities == []
    assert understanding.filters == {}
    assert understanding.required_fields == {}
    assert understanding.anchor_model is None

def test_ambiguous_person_filter_is_exposed_without_sales_context() -> None:
    understanding = QueryUnderstandingExtractor().understand("اعطني معلومات احمد")

    assert understanding.filters == {}
    assert understanding.required_fields == {}
    assert understanding.anchor_model is None
    assert understanding.ambiguities
    ambiguity = understanding.ambiguities[0]
    assert ambiguity.term == "احمد"
    assert set(ambiguity.candidates) == {"salesperson", "customer", "generic_person"}


def test_query_understanding_detects_broader_arabic_roles() -> None:
    understanding = QueryUnderstandingExtractor().understand(
        "اعرض مبيعات العميل والمنطقة والشركة والعملة وحالة الطلب والإجمالي"
    )

    assert understanding.intent == "sales_analysis"
    assert {"sales", "customer", "region", "company", "currency", "status", "total"}.issubset(
        set(understanding.entities)
    )
