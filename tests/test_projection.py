from pathlib import Path

from app.core.config import Settings
from app.projection.budget import BudgetRouter
from app.projection.pipeline import SchemaProjectionPipeline
from app.schema.adapters.postgres_sql_adapter import PostgresSqlSchemaAdapter
from app.schema.models import ProjectionOptions
from app.schema.orm_mapper import OrmMapper


QUERY = "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية"


def build_pipeline() -> SchemaProjectionPipeline:
    raw = PostgresSqlSchemaAdapter().load(Path("data/raw/odoo/schema.sql"))
    schema = OrmMapper().map(raw)
    return SchemaProjectionPipeline(schema, Settings(enable_dense_retrieval=False))


def test_projection_returns_query_guided_minimal_schema_without_hallucination() -> None:
    pipeline = build_pipeline()

    result = pipeline.run(QUERY, ProjectionOptions(debug=True))

    assert result.models == ["sale.order", "sale.order.line", "res.partner", "product.product"]
    assert result.debug is not None
    assert result.debug.metrics.hallucinated_models == 0
    assert result.debug.metrics.hallucinated_fields == 0
    assert result.debug.metrics.latency_ms <= 1500

    assert result.debug.query_understanding is not None
    assert result.debug.query_understanding.intent == "sales_analysis"
    assert set(result.debug.query_understanding.entities) == {"sales", "customer", "product", "quantity", "date"}
    assert result.debug.query_understanding.filters == {"month": "august", "salesperson": "أحمد"}
    assert result.debug.query_understanding.anchor_model == "sale.order"

    assert result.debug.paths == [
        ["sale.order", "res.partner"],
        ["sale.order", "sale.order.line"],
        ["sale.order", "sale.order.line", "product.product"],
    ]

    assert "sale.order" in result.schema_
    sale_order_fields = result.schema_["sale.order"]["fields"]
    assert set(sale_order_fields) == {"date_order", "partner_id", "sale_order_line_ids", "user_id"}

    partner_fields = sale_order_fields["partner_id"]["fields"]
    assert set(partner_fields) == {"name"}

    line_fields = sale_order_fields["sale_order_line_ids"]["fields"]
    assert set(line_fields) == {"product_id", "product_uom_qty"}

    product_fields = line_fields["product_id"]["fields"]
    assert set(product_fields) == {"name"}

    assert "res.country" not in result.models
    assert "res.company" not in result.models


def test_budget_router_clamps_user_supplied_limits() -> None:
    budget = BudgetRouter(Settings()).route(
        "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية",
        ProjectionOptions(
            max_models=100,
            max_depth=100,
            max_fields_per_model=100,
            max_total_fields=100,
            top_k_final=100,
        ),
    )

    assert budget.max_models == 8
    assert budget.max_depth == 4
    assert budget.max_fields_per_model == 12
    assert budget.max_total_fields == 50


def test_expanded_product_name_uses_template_path() -> None:
    from app.evaluation.metrics import collect_projected_fields

    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    pipeline = SchemaProjectionPipeline(OrmMapper().map(raw), Settings(enable_dense_retrieval=False))
    result = pipeline.run('sales product quantity', ProjectionOptions(debug=True))
    assert set(result.models) == {'sale.order', 'sale.order.line', 'product.product', 'product.template'}
    assert collect_projected_fields(result.schema_) == {
        'sale.order.sale_order_line_ids', 'sale.order.line.product_id',
        'sale.order.line.product_uom_qty', 'product.product.product_tmpl_id',
        'product.template.name',
    }
    assert result.debug.metrics.hallucinated_fields == 0
    fields = result.schema_['sale.order']['fields']['sale_order_line_ids']['fields']
    assert fields['product_id']['fields']['product_tmpl_id']['fields']['name']['type'] == 'char'


def test_expanded_customer_query_does_not_expand_country_or_company() -> None:
    from app.evaluation.metrics import collect_projected_fields

    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    pipeline = SchemaProjectionPipeline(OrmMapper().map(raw), Settings(enable_dense_retrieval=False))
    result = pipeline.run('sales customer total', ProjectionOptions(debug=True))
    assert set(result.models) == {'sale.order', 'res.partner'}
    assert collect_projected_fields(result.schema_) == {
        'sale.order.partner_id', 'sale.order.amount_total', 'res.partner.name',
    }


def test_expanded_golden_projection_quality(tmp_path: Path) -> None:
    from app.evaluation.expanded_golden_set import EXPANDED_GOLDEN_SET
    from app.evaluation.runner import run_evaluation

    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    pipeline = SchemaProjectionPipeline(OrmMapper().map(raw), Settings(enable_dense_retrieval=False))
    report = run_evaluation(pipeline, EXPANDED_GOLDEN_SET, tmp_path / 'expanded_report.json')
    summary = report['summary']
    for metric in ['model_precision_avg', 'model_recall_avg', 'field_precision_avg', 'field_recall_avg', 'relationship_validity_avg']:
        assert summary[metric] == 1.0
    assert summary['hallucination_count'] == 0
    assert summary['over_selection_count'] == 0
    assert summary['failed_path_count'] == 0
    assert summary['latency_p95_ms'] <= 1500


def test_expanded_role_paths_keep_customer_and_salesperson_separate() -> None:
    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    pipeline = SchemaProjectionPipeline(OrmMapper().map(raw), Settings(enable_dense_retrieval=False))
    result = pipeline.run('sales customer country salesperson', ProjectionOptions(debug=True))
    fields = result.schema_['sale.order']['fields']
    assert set(fields) == {'partner_id', 'user_id'}
    customer = fields['partner_id']['fields']
    assert set(customer) == {'name', 'country_id'}
    assert set(customer['country_id']['fields']) == {'name'}
    user = fields['user_id']['fields']
    assert set(user) == {'partner_id'}
    assert set(user['partner_id']['fields']) == {'name'}
    assert 'res.company' not in result.models


def test_expanded_role_projection_paths() -> None:
    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    pipeline = SchemaProjectionPipeline(OrmMapper().map(raw), Settings(enable_dense_retrieval=False))
    cases = [
        ('sales region', ['partner_id', 'state_id', 'name']),
        ('sales company', ['company_id', 'name']),
        ('sales currency', ['currency_id', 'name']),
        ('sales category', ['sale_order_line_ids', 'product_id', 'product_tmpl_id', 'categ_id', 'name']),
        ('sales salesperson', ['user_id', 'partner_id', 'name']),
    ]
    for query, path in cases:
        result = pipeline.run(query, ProjectionOptions(debug=True, max_depth=4))
        fields = result.schema_['sale.order']['fields']
        for index, name in enumerate(path):
            assert set(fields) == {name}, (query, fields)
            if index < len(path) - 1:
                fields = fields[name]['fields']
        assert result.debug.metrics.hallucinated_fields == 0


def test_expanded_role_path_respects_depth_budget() -> None:
    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    pipeline = SchemaProjectionPipeline(OrmMapper().map(raw), Settings(enable_dense_retrieval=False))
    result = pipeline.run('sales customer country', ProjectionOptions(debug=True, max_depth=1))
    assert 'res.country' not in result.models
    assert 'country_id' not in result.schema_['sale.order']['fields']['partner_id']['fields']


def test_focused_golden_set_preserves_relationship_paths() -> None:
    from app.evaluation.runner import run_evaluation

    report = run_evaluation(build_pipeline(), output_path=None)
    assert report['summary']['failed_path_count'] == 0
    assert report['summary']['over_selection_count'] == 0
    assert report['summary']['field_recall_avg'] == 1.0


def test_explicit_paths_do_not_report_models_pruned_by_budget() -> None:
    from app.evaluation.metrics import collect_projected_fields

    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    pipeline = SchemaProjectionPipeline(OrmMapper().map(raw), Settings(enable_dense_retrieval=False))
    result = pipeline.run('sales product', ProjectionOptions(debug=True, max_models=1))
    assert result.models == ['sale.order']
    assert result.schema_['sale.order']['fields'] == {}
    assert result.debug.paths == []
    assert result.debug.metrics.total_fields_after == len(collect_projected_fields(result.schema_)) == 0
