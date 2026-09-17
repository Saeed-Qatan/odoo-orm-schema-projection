# Project Overview

## Purpose

This repository contains a Python/FastAPI backend prototype for query-driven
Odoo ORM schema projection.

The backend receives a natural-language user query, identifies the smallest
relevant subset of an Odoo-like ORM schema, and returns a hierarchical schema
projection suitable for downstream LLM or agent workflows.

The project exists to avoid sending a full Odoo schema to an LLM. Instead, it
selects only the models, fields, and relationship paths needed by the query.

## Product Goal

Given a user query such as:

```text
أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية
```

The system should return only the schema required to answer that query, for
example:

- `sale.order`
- `sale.order.partner_id -> res.partner.name`
- `sale.order.sale_order_line_ids -> sale.order.line.product_id -> product.product.name`
- `sale.order.sale_order_line_ids -> sale.order.line.product_uom_qty`
- `sale.order.date_order`
- `sale.order.user_id`

It must not return unrelated branches such as customer country, company,
accounting, stock, or other Odoo models unless the query requires them.

## Current Scope

The current project is a backend prototype, not a complete Odoo integration.

Included:

- FastAPI service.
- PostgreSQL `schema.sql` ingestion.
- Odoo-like ORM schema mapping.
- Relationship graph construction with NetworkX.
- Query understanding based on aliases and deterministic rules.
- Hybrid retrieval using BM25, fuzzy matching, and optional dense retrieval.
- Query-guided graph traversal.
- Field-level schema pruning.
- Hierarchical JSON schema projection.
- Debug output with query understanding, retrieval results, relationship paths,
  confidence scores, removed fields, and latency metrics.
- Local golden-set evaluation.

Excluded for now:

- Running or connecting to Odoo itself.
- Executing SQL against business data.
- Generating Odoo domains.
- Building a frontend UI.
- Production authentication or tenant isolation.
- Dense retrieval as the default path.

## Core Pipeline

The intended request flow is:

```text
User Query
-> Query Understanding
-> Hybrid Retrieval
-> Schema Linking
-> Query-Guided Graph Traversal
-> Field-Level Pruning
-> Strict Validation
-> Hierarchical ORM Schema Projection
```

The pipeline must remain deterministic for schema selection. Do not use an LLM
to choose models, fields, or relationship paths in the core projection flow.

## Source Data

The default runnable schema is:

```text
data/raw/odoo/schema.sql
```

It is a focused sample containing:

- `res_partner`
- `product_product`
- `sale_order`
- `sale_order_line`

The sample is intentionally small and exists to prove the backend pipeline.

A larger downloaded schema also exists:

```text
data/raw/odoo/schema.full.sql
```

That file is useful for parser experiments, but it is not the default demo
source because it does not contain the sales tables used by the current golden
queries.

## Generated / Processed Data

Generated schema and graph snapshots live under:

```text
data/processed/
```

Important files:

- `data/processed/odoo_orm_schema.json`
- `data/processed/odoo_schema_graph.json`
- `data/processed/evaluation_report.json`

These files are derived from source schema, aliases, and pipeline logic. If the
mapper, aliases, or schema source changes, regenerate the processed outputs.

## Alias Configuration

Query understanding and schema keywords are configured in:

```text
data/config/schema_aliases.json
```

Use this file for Arabic/English synonyms, entities, months, filters, and
model/field aliases. Prefer updating this configuration over hardcoding new
synonyms directly in Python.

## Quality Targets

The prototype should optimize for:

1. Zero hallucinated models.
2. Zero hallucinated fields.
3. Valid relationship paths only.
4. Query-guided traversal without unrelated expansion.
5. Field-level pruning.
6. P95 latency under `1500ms` for local golden-set requests.
7. Clear debug output for inspection and evaluation.

Current local golden-set expectations:

- Model precision/recall should remain `1.0 / 1.0`.
- Field precision/recall should remain `1.0 / 1.0`.
- Relationship validity should remain `1.0`.
- Hallucination count should remain `0`.
- Over-selection count should remain `0`.

## Public API

The currently supported API surface is:

```http
GET /health
GET /api/v1/schema/models
GET /api/v1/schema/models/{model_name}
POST /api/v1/project-schema
```

Do not change these endpoints or response shapes without updating the API
specification and tests.

## Verification Commands

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run evaluation:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner
```

Run the local API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Important Constraints

- Keep implementation small and scoped.
- Do not introduce new dependencies without clear justification.
- Do not execute user SQL.
- Do not connect to production ERP databases.
- Do not commit secrets or `.env` values.
- Do not bypass the projection pipeline layers for convenience.
- Any architecture-changing decision must be recorded in
  `.agents/CURRENT_STATE.md`.

## Evidence Notes

When discussing the project:

- Use **OBSERVED** for facts verified from repository files, tests, or generated
  reports.
- Use **INFERRED** for likely conclusions based on repository evidence.
- Use **PROPOSED** for recommendations or future work.

Do not present inferred or proposed behavior as observed fact.

