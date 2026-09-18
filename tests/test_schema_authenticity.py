from pathlib import Path

from app.schema.authenticity import evaluate_schema_source


def test_expanded_schema_is_not_marked_as_authentic_odoo_export() -> None:
    report = evaluate_schema_source(Path("data/raw/odoo/schema.expanded.sql"))

    assert report["is_authentic_candidate"] is False
    assert report["synthetic_marker_found"] is True
    assert "purchase.order" in report["missing_scale_models"]
    assert "stock.picking" in report["missing_scale_models"]


def test_focused_schema_is_not_ready_for_authentic_scale_adoption() -> None:
    report = evaluate_schema_source(Path("data/raw/odoo/schema.sql"))

    assert report["is_authentic_candidate"] is False
    assert "res.users" in report["missing_core_models"]
    assert "account.move" in report["missing_scale_models"]