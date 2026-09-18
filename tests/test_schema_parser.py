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


def test_pglast_handles_defaults_primary_keys_and_inheritance() -> None:
    raw = PostgresSqlSchemaAdapter()._load_with_pglast("""
        CREATE TABLE parent (id integer NOT NULL, name text);
        CREATE TABLE child (parent_id integer) INHERITS (parent);
        ALTER TABLE parent ALTER COLUMN id SET DEFAULT nextval('parent_seq');
        ALTER TABLE parent ADD CONSTRAINT parent_pkey PRIMARY KEY (id);
        ALTER TABLE child ADD CONSTRAINT child_pkey PRIMARY KEY (id);
        ALTER TABLE child ADD CONSTRAINT child_parent_fk
            FOREIGN KEY (parent_id) REFERENCES parent(id);
    """)
    assert raw.tables['parent'].primary_key == ['id']
    child = raw.tables['child']
    assert {c.name for c in child.columns} == {'id', 'name', 'parent_id'}
    assert child.primary_key == ['id']
    assert next(c for c in child.columns if c.name == 'id').primary_key
    assert len(raw.foreign_keys) == 1


def test_full_schema_uses_pglast_and_resolves_foreign_keys() -> None:
    raw = PostgresSqlSchemaAdapter()._load_with_pglast(
        Path('data/raw/odoo/schema.full.sql').read_text(encoding='utf-8')
    )
    assert len(raw.tables) == 168
    assert raw.tables['res_partner'].primary_key == ['id']
    for fk in raw.foreign_keys:
        assert fk.table in raw.tables
        assert fk.ref_table in raw.tables
        assert fk.column in {c.name for c in raw.tables[fk.table].columns}
        assert fk.ref_column in {c.name for c in raw.tables[fk.ref_table].columns}


def test_regex_full_schema_matches_pglast_structure() -> None:
    sql = Path('data/raw/odoo/schema.full.sql').read_text(encoding='utf-8')
    adapter = PostgresSqlSchemaAdapter()
    expected = adapter._load_with_pglast(sql)
    actual = adapter._load_with_regex(sql)
    assert set(actual.tables) == set(expected.tables)
    for name, table in expected.tables.items():
        assert {c.name for c in actual.tables[name].columns} == {c.name for c in table.columns}
        assert set(actual.tables[name].primary_key) == set(table.primary_key)
        assert {c.name: (c.nullable, c.primary_key) for c in actual.tables[name].columns} == {
            c.name: (c.nullable, c.primary_key) for c in table.columns
        }
    identity = lambda fk: (fk.table, fk.column, fk.ref_table, fk.ref_column)
    assert {identity(fk) for fk in actual.foreign_keys} == {identity(fk) for fk in expected.foreign_keys}


def test_regex_does_not_cross_alter_statement_boundaries() -> None:
    raw = PostgresSqlSchemaAdapter()._load_with_regex('''
        CREATE TABLE parent (id integer PRIMARY KEY);
        CREATE TABLE unrelated (id integer);
        CREATE TABLE child (id integer, parent_id integer);
        ALTER TABLE unrelated OWNER TO demo;
        ALTER TABLE child ADD CONSTRAINT child_parent_fk
            FOREIGN KEY (parent_id) REFERENCES parent(id);
        ALTER TABLE child ADD CONSTRAINT child_pkey PRIMARY KEY (id);
    ''')
    assert raw.foreign_keys[0].table == 'child'
    assert raw.tables['child'].primary_key == ['id']
    assert next(c for c in raw.tables['child'].columns if c.name == 'id').nullable is False


def test_expanded_schema_maps_sales_and_product_relationships() -> None:
    from app.schema.orm_mapper import OrmMapper

    raw = PostgresSqlSchemaAdapter().load(Path('data/raw/odoo/schema.expanded.sql'))
    assert len(raw.tables) == 173
    for fk in raw.foreign_keys:
        assert fk.column in {c.name for c in raw.tables[fk.table].columns}
        assert fk.ref_column in {c.name for c in raw.tables[fk.ref_table].columns}
    orm = OrmMapper().map(raw)
    relations = {
        ('sale.order', 'partner_id'): 'res.partner',
        ('sale.order', 'user_id'): 'res.users',
        ('sale.order', 'company_id'): 'res.company',
        ('sale.order', 'currency_id'): 'res.currency',
        ('sale.order.line', 'order_id'): 'sale.order',
        ('sale.order.line', 'product_id'): 'product.product',
        ('product.product', 'product_tmpl_id'): 'product.template',
        ('product.template', 'categ_id'): 'product.category',
        ('product.category', 'parent_id'): 'product.category',
    }
    for (model, field), target in relations.items():
        assert orm.models[model].fields[field].type == 'many2one'
        assert orm.models[model].fields[field].relation == target
    assert 'name' not in orm.models['product.product'].fields
    assert 'name' in orm.models['product.template'].fields
    assert orm.models['sale.order'].fields['sale_order_line_ids'].inverse == 'order_id'
    assert orm.models['sale.order'].fields['sale_order_line_ids'].inferred is True
    sql = Path('data/raw/odoo/schema.expanded.sql').read_text(encoding='utf-8')
    fallback = PostgresSqlSchemaAdapter()._load_with_regex(sql)
    assert set(fallback.tables) == set(raw.tables)
    identity = lambda fk: (fk.table, fk.column, fk.ref_table, fk.ref_column)
    assert {identity(fk) for fk in fallback.foreign_keys} == {identity(fk) for fk in raw.foreign_keys}
