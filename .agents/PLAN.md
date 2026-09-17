# Backend Prototype Development Plan: Odoo ORM Schema Projection

## Current Progress Snapshot

The project is currently stabilizing the backend prototype and organizing repository-local Codex instructions.

Confirmed current state from repository files:

- The backend prototype exists and is split into clear layers.
- The core API is implemented with FastAPI.
- The small `schema.sql` file is the default runtime schema source.
- `schema.full.sql` exists for parser experiments, but it is not the current demo source.
- Aliases now live in `data/config/schema_aliases.json` instead of relying only on hardcoded rules.
- `pglast` is used as the primary parsing path with a regex fallback.
- Graph traversal and field-level pruning exist.
- The evaluation runner and golden set exist.
- Latest verified checks: `pytest` passed, and evaluation ran on 20 cases with no hallucination or over-selection.
- Current work is focused on documentation and Codex instructions, then backend development continues.

## Summary

We are building a Python/FastAPI backend that reads an Odoo PostgreSQL `schema.sql`, converts it into an Odoo-like `ORM-like Schema`, builds a relationship graph, then receives a user query and returns the smallest hierarchical schema needed to answer that query.

The goal is not to send the full Odoo schema to an LLM. The goal is to project a small, accurate schema subset based on the question.

Success criteria:

- Local response latency stays below `1500ms` on the golden set.
- `hallucinated_models = 0`.
- `hallucinated_fields = 0`.
- Output relationships must be real or clearly inferred from foreign keys.
- Traversal must be query-guided and must not expand into unrelated models.
- Pruning must happen at the field level, not only at the model level.

## Lessons From Reviewed Repositories

Lessons adopted from reviewing similar projects, without documenting repository names as official source facts inside this repo:

- Split the pipeline into small stages: parsing, mapping, retrieval, linking, traversal, pruning, projection.
- Keep aliases and synonyms outside the code as much as possible so they can be expanded safely.
- Treat retrieval as a helper, not as a final authority without validation.
- Build evaluation early to measure hallucination, over-selection, relationship validity, and latency.
- Keep the output hierarchical and explicit so a downstream agent or LLM can understand the relationships.
- Prefer conservative schema projection when confidence is low instead of expanding randomly.

## Libraries And Algorithms

Currently used or included in the project design:

- Backend: `FastAPI`, `uvicorn`, `pydantic`, `pydantic-settings`.
- Schema parsing: `pglast` with regex fallback.
- ORM-like mapping: table-name to Odoo-like model-name conversion, FK to `many2one`, and inferred `one2many` relations.
- Graph: `networkx` for representing models, fields, and relationships, plus traversal/path finding.
- Sparse retrieval: `rank-bm25`.
- Fuzzy matching: `rapidfuzz`.
- Hybrid retrieval structure: RRF and result merging.
- Dense retrieval: available as an optional path, but not enabled by default.
- Testing/evaluation: `pytest`, golden set, evaluation report.

## Current Architecture

```text
HTTP Request
-> FastAPI routes
-> SchemaProjectionPipeline
-> Query Understanding
-> Retrieval
-> Schema Linking
-> Query-Guided Graph Traversal
-> Field-Level Pruning
-> Strict Validation
-> Hierarchical ORM Schema Projection
```

Important files:

```text
app/main.py
app/api/routes/health.py
app/api/routes/schema.py
app/api/routes/projection.py
app/schema/models.py
app/schema/aliases.py
app/schema/adapters/postgres_sql_adapter.py
app/schema/orm_mapper.py
app/schema/repository.py
app/graph/builder.py
app/graph/traverser.py
app/graph/ranker.py
app/retrieval/bm25.py
app/retrieval/fuzzy.py
app/retrieval/hybrid.py
app/retrieval/rrf.py
app/projection/query_understanding.py
app/projection/linker.py
app/projection/pipeline.py
app/projection/pruner.py
app/projection/projector.py
app/evaluation/golden_set.py
app/evaluation/metrics.py
app/evaluation/runner.py
```

Data sources:

```text
data/raw/odoo/schema.sql
data/raw/odoo/schema.full.sql
data/config/schema_aliases.json
data/processed/odoo_orm_schema.json
data/processed/odoo_schema_graph.json
data/processed/evaluation_report.json
```

## What Is Done

### Phase 1 — Foundation

- [x] Install the core backend and evaluation dependencies.
- [x] Move settings to `app/core/config.py`.
- [x] Add `.env.example`.
- [x] Add `GET /health`.
- [x] Keep the operational database outside the current core pipeline.

### Phase 2 — Schema Ingestion

- [x] Place the default runtime schema in `data/raw/odoo/schema.sql`.
- [x] Build `PostgresSqlSchemaAdapter`.
- [x] Enable `pglast` as the primary parsing path.
- [x] Keep regex fallback when advanced parsing fails.
- [x] Extract tables, columns, types, primary keys, and foreign keys.
- [x] Represent the raw schema with Pydantic models.

### Phase 3 — ORM-like Schema Mapping

- [x] Build `OrmMapper`.
- [x] Convert table names into Odoo-like models such as `sale.order` and `res.partner`.
- [x] Convert foreign keys into `many2one` fields.
- [x] Infer reverse `one2many` fields with `inferred=true`.
- [x] Save output to `data/processed/odoo_orm_schema.json`.
- [x] Generate hierarchy at request time instead of storing repeated hierarchy.

### Phase 4 — Schema Graph

- [x] Build `SchemaGraphBuilder` with `networkx`.
- [x] Represent models, fields, and relationships as nodes and edges.
- [x] Build `GraphTraverser` for paths and bounded-depth traversal.
- [x] Save graph snapshot to `data/processed/odoo_schema_graph.json`.

### Phase 5 — Retrieval And Aliases

- [x] Build a searchable corpus for models and fields.
- [x] Build `BM25Retriever`.
- [x] Build `FuzzyRetriever`.
- [x] Build hybrid retrieval structure and RRF.
- [x] Move aliases to `data/config/schema_aliases.json`.
- [x] Add `AliasCatalog` to load aliases from JSON.
- [~] Dense retrieval exists as an optional path, but it is not the default and has not been adopted as a production path.

### Phase 6 — Query Pipeline

- [x] Build `SchemaProjectionPipeline`.
- [x] Build `QueryUnderstandingExtractor` for intent, entities, filters, and requested fields.
- [x] Build schema linking.
- [x] Enable query-guided traversal guard.
- [x] Enable field-level pruning.
- [x] Prevent unrelated models from entering the output unless they are necessary bridge models.
- [x] Return hierarchical ORM schema output.
- [x] Prevent unknown models and fields from being returned.

### Phase 7 — API

- [x] Add `POST /api/v1/project-schema`.
- [x] Add `GET /api/v1/schema/models`.
- [x] Add `GET /api/v1/schema/models/{model_name}`.
- [x] Support `debug` output for query understanding, paths, removed fields, and metrics.

### Phase 8 — Quality, Speed, Hallucination Control

- [x] Load schema and graph from files/memory instead of rebuilding them unpredictably inside request logic.
- [x] Prevent dense indexes from being built during the default request path.
- [x] Add over-selection guard inside traversal/pruning.
- [x] Add confidence/debug structures.
- [x] Measure latency, reduction, and hallucination in debug/evaluation.
- [x] Strict request timeout is verified by a test that returns `504` when the timeout is exceeded.
- [x] Rate limiting is verified by `429` tests on projection and schema read endpoints.

### Phase 9 — Evaluation

- [x] Create a golden set of 20 questions.
- [x] Define expected models, fields, and relationship paths.
- [x] Measure model precision/recall.
- [x] Measure field precision/recall on nested fields.
- [x] Measure relationship validity.
- [x] Measure reduction ratio and latency p50/p95.
- [x] Measure hallucination and over-selection.
- [x] Generate `data/processed/evaluation_report.json`.

### Phase 10 — Codex Instruction Layer

- [x] Create `AGENTS.md`.
- [x] Create `.agents/PROJECT.md`.
- [x] Create `.agents/ARCHITECTURE.md`.
- [x] Create `.agents/RULES.md`.
- [x] Create `.agents/CURRENT_STATE.md`.
- [x] Create `.agents/TASKS.md`.
- [x] Create `.agents/PLAN.md`.
- [x] Remove the old nested structure from the intended plan.
- [~] Commit/push documentation changes is still required after final review.

## Current Phase

The current phase is stabilizing the plan and documentation after backend prototype progress.

The immediate goal is not to add a new feature. The goal is to keep `.agents/PLAN.md` accurate as the single source of truth, then keep marking tasks as done when they are actually implemented and verified.

## Next Steps

### Documentation Stabilization

- [ ] Review `.agents/PLAN.md` after updates.
- [ ] Update `.agents/CURRENT_STATE.md` if project state changes after accepting the plan.
- [ ] Commit/push instruction and documentation changes on branch `develop`.

### Backend Hardening

- [x] Review `app/core/rate_limit.py` and verify that rate limiting is active on endpoints.
- [x] Add request-limit tests for query length and clamping of `max_depth`, `max_models`, and `max_total_fields`.
- [x] Verify internal request timeout with a `504` test and fix `asyncio.TimeoutError` handling.
- [x] Add protection and limit tests in `tests/test_api.py` and `tests/test_projection.py`.

### Odoo Scale Preparation

- [ ] Prepare a larger schema that contains real sales models instead of only the focused sample.
- [ ] Verify that the parser handles the larger schema without breaking.
- [ ] Expand aliases to cover more Odoo scenarios.
- [ ] Expand the golden set after introducing the larger schema.
- [ ] Run evaluation and compare p50/p95 latency, hallucination, and over-selection.

### Retrieval Improvements

- [ ] Keep dense retrieval disabled by default until there is a proven need.
- [ ] Evaluate dense retrieval on the golden set after introducing the larger schema.
- [ ] Adopt dense retrieval only if it improves recall without unacceptable hallucination or latency cost.

## Test Plan

For the current plan/documentation update:

- [ ] Read `.agents/PLAN.md` after modification.
- [ ] Confirm completed items are marked with `[x]`.
- [ ] Confirm partially completed items are marked with `[~]`.
- [ ] Confirm next items are marked with `[ ]`.
- [ ] Confirm changes are limited to documentation files.

For backend development:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m app.evaluation.runner
```

## Assumptions And Decisions

- The project is backend-only in this phase.
- We do not generate Odoo domains yet.
- We do not execute SQL from the user query.
- We do not connect to an operational ERP database.
- We do not add dependencies without a clear reason.
- `data/raw/odoo/schema.sql` is the current default runtime source.
- `data/raw/odoo/schema.full.sql` is not the current demo source because, as-is, it does not support the current sales questions.
- `.agents/PLAN.md` is the only accepted plan source for this repository.
- Details of the five reviewed repositories are not documented inside this repo, so the plan records only general lessons without names or unverified claims.

