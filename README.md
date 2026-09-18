# Odoo ORM Schema Projection

Prototype backend for query-driven Odoo ORM schema projection.

The service reads PostgreSQL `schema.sql`, maps it to an Odoo-like ORM schema, builds a relationship graph, and returns the smallest hierarchical schema needed for a user query.

## Current Backend Scope

- FastAPI API.
- PostgreSQL schema ingestion from `data/raw/odoo/schema.sql`.
- ORM-like schema generation in `data/processed/odoo_orm_schema.json`.
- NetworkX graph generation in `data/processed/odoo_schema_graph.json`.
- Hybrid retrieval with BM25, fuzzy matching, and optional dense embeddings.
- RRF ranking, graph traversal, pruning, strict validation, and latency metrics.
- Rate limits for projection and schema read endpoints.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

```http
GET /health
GET /api/v1/schema/models
GET /api/v1/schema/models/{model_name}
POST /api/v1/project-schema
```

Example request:

```json
{
  "query": "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية",
  "options": {
    "debug": true,
    "max_models": 5,
    "max_depth": 3,
    "max_total_fields": 30
  }
}
```

## Quality Targets

- P95 latency should stay under 1500 ms for normal requests.
- Hallucinated models and fields must stay at 0.
- Every returned relationship must exist in the ORM-like schema.
- The projection should return only fields needed by the query or fields required to preserve relationship paths.

## Tests

```bash
pytest
```
## Demo Dataset Notes

The default runnable dataset is `data/raw/odoo/schema.sql`, a focused local sample that includes:

- `sale.order`
- `sale.order.line`
- `res.partner`
- `product.product`

The full Prisma Odoo sample was downloaded to `data/raw/odoo/schema.full.sql` for broader parser experiments. It currently parses successfully, but it does not include `sale_order` tables, so the focused sample remains the default source for the sales-query demo.

## Current Verification Snapshot

On the focused sample, the Arabic demo query returns `sale.order` as the hierarchy root with `partner_id.name`, `sale_order_line_ids.product_id.name`, `sale_order_line_ids.product_uom_qty`, `date_order`, and `user_id`.

Latest local check:

```bash
.\.venv\Scripts\python.exe -m pytest
```

Result: 6 passed, with zero hallucinated models/fields in the projection test and API check latency around 1-2 ms on the sample.
## Evaluation

Run the local golden-set evaluation:

```bash
.\.venv\Scripts\python.exe -m app.evaluation.runner
```

The runner writes `data/processed/evaluation_report.json` and reports model/field precision and recall, relationship validity, reduction ratio, P50/P95 latency, hallucination count, and over-selection count.

Current local golden-set snapshot:

- 20 cases.
- Model precision/recall: 1.0 / 1.0.
- Field precision/recall: 1.0 / 1.0.
- Relationship validity: 1.0.
- Hallucination count: 0.
- Over-selection count: 0.
- P95 latency: about 1 ms on the focused sample.

## Alias Configuration

Query understanding and schema keywords are driven by `data/config/schema_aliases.json`. Update that file to add Arabic/English synonyms, entities, months, filters, and model/field aliases without changing Python code.


## Expanded Schema Test Fixture (V2)

`data/raw/odoo/schema.expanded.sql` preserves the existing `schema.full.sql`
content and appends five synthetic tables: `sale_order`, `sale_order_line`,
`product_product`, `product_template`, and `product_category`.
This is not an authentic Odoo sales export and contains no business records.
Do not execute it against an operational database.

The fixture contains 173 tables, 1699 columns including inherited columns, and
525 foreign keys. Parser and mapper tests validate the added relationships.
Product names live on `product_template`; salesperson IDs reference `res_users`.
The runtime default remains `schema.sql`. Query aliases and golden expectations
must be adapted before adopting the expanded fixture for API requests.

## Expanded Projection Verification

Product entities support schema_variants in the alias JSON. The extractor chooses
a variant only when its required fields exist in the active schema. Expanded
product names resolve through product_tmpl_id to product.template.name; the
focused sample retains its direct name field.

The expanded golden set lives in app/evaluation/expanded_golden_set.py, with a
separate report in data/processed/evaluation_report.expanded.json. Its six initial
cases passed exact model/field expectations, including the Arabic demo query.
Country/company/category and explicit salesperson-name query support still need
role-specific mapping and additional evaluation. Do not switch the default merely
because schema parsing succeeds.

## Role-Specific Expanded Queries

Initial sales-context support now covers customer country/region, order
company/currency, product category and salesperson names. Explicit field paths
prevent customer geography leaking into salesperson branches. Debug understanding
includes an additive field_paths list. Product category needs max_depth=4.

Run independent evaluation without replacing focused schema caches:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --expanded
```

Fourteen expanded cases passed exact model/field expectations, with no
hallucination, over-selection or missing paths. Arbitrary ambiguous questions
are not certified. Default API source remains the focused fixture.

## Run The Expanded API Separately

The default entrypoint remains app.main:app. Use the expanded synthetic fixture
with independent ORM/graph caches and an independent index directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.expanded:app --host 127.0.0.1 --port 8002 --reload
```

Swagger: http://127.0.0.1:8002/docs
Projection: POST http://127.0.0.1:8002/api/v1/project-schema

Example role-specific request:

```json
{
  "query": "أعطني المبيعات مع اسم العميل وبلد العميل واسم المندوب",
  "options": {"debug": true, "max_models": 5, "max_depth": 3}
}
```

For product-category requests, set max_depth to 4. Expanded source definitions
remain a synthetic fixture, not authentic Odoo ERP metadata.

ORM cache reuse now requires source identity/content hashes and artifact hash
validation, including parser/mapper/model/alias inputs. Local metadata sidecars
are ignored by Git. Old caches without metadata are rebuilt once. Expanded
ORM/graph artifacts have .expanded.json names and do not replace focused files.
