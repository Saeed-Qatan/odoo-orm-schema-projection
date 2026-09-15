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


