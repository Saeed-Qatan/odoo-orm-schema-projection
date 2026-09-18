# Backend Prototype Development Plan: Odoo ORM Schema Projection

## Current Progress Snapshot

This repository is on branch `v2`.

The backend prototype is stable enough for focused and opt-in expanded schema testing. The current source of truth for the project plan is this file:

```text
.agents/PLAN.md
```

The root `plan.md` file was removed intentionally. Do not recreate it unless the project plan ownership decision changes.

Confirmed progress:

- The default focused API runtime is implemented and remains unchanged.
- The opt-in expanded API runtime is implemented for broader schema testing.
- The parser uses `pglast` first and keeps a regex fallback.
- ORM-like mapping, graph construction, retrieval, linking, traversal, pruning, projection, validation, API endpoints, evaluation, and instruction files exist.
- Expanded V2 changes were committed and pushed to remote branch `v2`.
- The expanded schema is synthetic: it is useful for development tests, but it is not a genuine Odoo sales export.

Latest verified snapshot from repository history:

- Full test suite: `36 passed`, with two dependency deprecation warnings.
- Default evaluation: 20 cases, zero hallucination, zero over-selection, zero failed paths.
- Expanded evaluation: 14 cases, zero hallucination, zero over-selection, zero failed paths.
- Live expanded runtime check on `127.0.0.1:8002`: health ok, 173 models, and Arabic role projection returned separate customer/country and salesperson branches.

These are historical verified results. Re-run the checks before claiming a new current verification snapshot.

## Product Goal

Build a Python/FastAPI backend that reads an Odoo-like PostgreSQL schema, converts it into an ORM-like representation, builds a relationship graph, then receives a user query and returns only the smallest hierarchical schema subset needed to answer that query.

The system should avoid sending a full Odoo schema to an LLM. It should project only the relevant models, fields, and relationship paths.

Example user query:

```text
أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية
```

Expected projection shape:

```text
sale.order
├── date_order
├── user_id
├── partner_id -> res.partner.name
└── sale_order_line_ids -> sale.order.line
    ├── product_uom_qty
    └── product_id -> product.product.name
```

In the expanded runtime, product name may be resolved through:

```text
sale.order.line.product_id -> product.product.product_tmpl_id -> product.template.name
```

depending on the active schema source.

## Success Criteria

- `hallucinated_models = 0`.
- `hallucinated_fields = 0`.
- Relationship paths are valid and come from the ORM-like schema.
- Traversal is query-guided and does not expand into unrelated branches.
- Pruning happens at field level, not only at model level.
- Local P95 latency stays below `1500ms` on supported golden sets.
- Debug output explains understanding, selected paths, removed fields, metrics, and latency.

## Architecture

```text
HTTP Request
-> FastAPI routes
-> SchemaProjectionPipeline
-> Query Understanding
-> Retrieval
-> Schema Linking
-> Query-Guided Traversal
-> Field-Level Pruning
-> Strict Validation
-> Hierarchical ORM Schema Projection
```

Important modules:

```text
app/application.py
app/main.py
app/expanded.py
app/app_state.py
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
app/evaluation/expanded_golden_set.py
app/evaluation/metrics.py
app/evaluation/runner.py
```

Important data files:

```text
data/raw/odoo/schema.sql
data/raw/odoo/schema.full.sql
data/raw/odoo/schema.expanded.sql
data/config/schema_aliases.json
data/processed/odoo_orm_schema.json
data/processed/odoo_schema_graph.json
data/processed/odoo_orm_schema.expanded.json
data/processed/odoo_schema_graph.expanded.json
data/processed/evaluation_report.json
data/processed/evaluation_report.expanded.json
```

## Libraries And Algorithms

- Backend: `FastAPI`, `uvicorn`, `pydantic`, `pydantic-settings`.
- Schema parsing: `pglast` with regex fallback.
- ORM-like mapping: table-to-model conversion, `many2one` from foreign keys, inferred `one2many` reverse relations.
- Graph: `networkx` for relationship graph construction and traversal.
- Sparse retrieval: `rank-bm25`.
- Fuzzy retrieval: `rapidfuzz`.
- Hybrid retrieval: RRF-style result merging.
- Dense retrieval: optional and disabled by default.
- Testing and evaluation: `pytest`, golden sets, JSON evaluation reports.

## Lessons From Reviewed Repositories

The repository does not currently document the names or exact findings from the five reviewed repositories, so this plan records only general lessons:

- Split the pipeline into explicit stages.
- Keep aliases and synonyms outside Python code when practical.
- Treat retrieval as a helper, not as final authority.
- Validate every selected model, field, and relationship path.
- Measure hallucination, over-selection, relationship validity, latency, and reduction ratio early.
- Prefer conservative projection when confidence is low.

## Done

### Phase 1 - Foundation

- [x] Install core backend and evaluation dependencies.
- [x] Move settings to `app/core/config.py`.
- [x] Add `.env.example`.
- [x] Add `GET /health`.
- [x] Keep operational database access outside the current pipeline.

### Phase 2 - Schema Ingestion

- [x] Add focused runtime schema at `data/raw/odoo/schema.sql`.
- [x] Add full parser experiment source at `data/raw/odoo/schema.full.sql`.
- [x] Add synthetic expanded source at `data/raw/odoo/schema.expanded.sql`.
- [x] Build `PostgresSqlSchemaAdapter`.
- [x] Parse with `pglast` first.
- [x] Keep regex fallback.
- [x] Extract tables, columns, primary keys, foreign keys, inherited columns, and column-level references.
- [x] Add tests for parser behavior and fallback parity.

### Phase 3 - ORM-like Mapping

- [x] Build `OrmMapper`.
- [x] Convert table names into Odoo-like model names.
- [x] Convert foreign keys into `many2one` fields.
- [x] Infer reverse `one2many` fields with `inferred=true`.
- [x] Save generated ORM schema artifacts.
- [x] Add source-specific cache metadata and artifact hash validation.

### Phase 4 - Schema Graph

- [x] Build `SchemaGraphBuilder` with `networkx`.
- [x] Represent models, fields, and relationships.
- [x] Build bounded traversal helpers.
- [x] Save graph snapshots for focused and expanded runtimes.

### Phase 5 - Retrieval And Aliases

- [x] Build searchable schema corpus.
- [x] Build BM25 retriever.
- [x] Build fuzzy retriever.
- [x] Build hybrid/RRF result merging.
- [x] Move aliases to `data/config/schema_aliases.json`.
- [x] Add schema-aware alias variants and explicit field paths.
- [~] Keep dense retrieval available but disabled by default.

### Phase 6 - Query Projection Pipeline

- [x] Build `SchemaProjectionPipeline`.
- [x] Build query understanding for intent, entities, filters, fields, and explicit field paths.
- [x] Validate field paths against the active schema.
- [x] Link query concepts to schema candidates.
- [x] Enforce query-guided traversal.
- [x] Enforce depth and budget limits.
- [x] Prune fields after traversal.
- [x] Preserve role-scoped relationship occurrences so customer partner fields do not leak into salesperson partner fields.
- [x] Remove incomplete paths after budget pruning.
- [x] Return hierarchical JSON schema output.

### Phase 7 - API

- [x] Add `POST /api/v1/project-schema`.
- [x] Add `GET /api/v1/schema/models`.
- [x] Add `GET /api/v1/schema/models/{model_name}`.
- [x] Add debug output for understanding, paths, removed fields, metrics, and latency.
- [x] Add `app.application.create_app(settings)`.
- [x] Keep `app.main:app` as the focused runtime.
- [x] Add `app.expanded:app` as the opt-in expanded runtime.

### Phase 8 - Protection And Runtime Behavior

- [x] Add rate limiting tests for projection and schema read endpoints.
- [x] Add query length and budget limit tests.
- [x] Add timeout handling that returns `504`.
- [x] Prevent accidental cache reuse across different schema sources.
- [x] Log graph snapshot write failures instead of silently swallowing them.

### Phase 9 - Evaluation

- [x] Add default golden set with 20 cases.
- [x] Add expanded golden set with 14 cases.
- [x] Measure model precision/recall.
- [x] Measure nested field precision/recall.
- [x] Measure relationship validity.
- [x] Measure reduction ratio and latency p50/p95.
- [x] Measure hallucination, over-selection, and failed paths.
- [x] Generate default and expanded JSON evaluation reports.

### Phase 10 - Codex Instruction Layer

- [x] Create `AGENTS.md`.
- [x] Create `.agents/PROJECT.md`.
- [x] Create `.agents/ARCHITECTURE.md`.
- [x] Create `.agents/RULES.md`.
- [x] Create `.agents/CURRENT_STATE.md`.
- [x] Create `.agents/TASKS.md`.
- [x] Create `.agents/PLAN.md`.
- [x] Remove old nested instruction directories from the intended structure.
- [x] Remove root `plan.md` and keep `.agents/PLAN.md` as the only official plan source.

### Phase 11 - V1 And V2 Git State

- [x] Save previous stable backend snapshot on remote branch `v1`.
- [x] Create branch `v2` for schema expansion work.
- [x] Commit expanded runtime and schema work on `v2`.
- [x] Push `v2` to the remote repository.

## Current Phase

The current phase is V2 expansion hardening.

The project can now test broader schema relationships through the opt-in expanded runtime, but it should not claim full Odoo fidelity yet because the sales/product additions in `schema.expanded.sql` are synthetic.

## Next Development Steps

### Step 1 - Synchronize Documentation

- [x] Review `.agents/PLAN.md` against actual V2 progress.
- [x] Update stale statements about uncommitted/unpushed work.
- [x] Make the completed and remaining work explicit.

### Step 2 - Arabic Query Understanding Expansion

- [x] Add more Arabic aliases for common misspellings and variants.
- [x] Add tests for typo-like cases such as `المندو` vs `المندوب`.
- [x] Improve role detection for salesperson, customer, country, branch, company, currency, category, product, quantity, status, total, and date on supported aliases.
- [x] Keep new Arabic aliases in `data/config/schema_aliases.json`; Python logic is limited to conservative fuzzy matching.

### Step 3 - Ambiguity Handling

- [x] Decide how to represent ambiguous phrases such as `أحمد`: unsupported with debug ambiguity unless sales/customer/salesperson context is present.
- [x] Add debug output that exposes ambiguity when confidence is not enough.
- [x] Add golden/evaluation and focused tests for typo, broader Arabic roles, ambiguity and unsupported questions.
- [x] Avoid expanding unrelated schema branches when ambiguity exists.

### Step 4 - Budget And Negative-Case Coverage

- [x] Add tests for low `max_depth`, `max_models`, and `max_total_fields` on expanded relationship paths.
- [x] Add tests for unsupported requests and unfulfillable paths.
- [x] Confirm incomplete paths are removed consistently from output and debug.

### Step 5 - Mapper Fidelity Review

- [x] Review whether current field naming and inferred reverse relation naming are close enough to Odoo expectations.
- [x] Document known differences between synthetic fixture behavior and real Odoo schema behavior.
- [x] Add mapper tests for confirmed fidelity gaps.

### Step 6 - Authentic Odoo Sales Schema

Current status: blocked on an external authentic Odoo schema export. The repository now has a readiness checker, but it cannot turn the synthetic fixture into a genuine export.

- [ ] Obtain or generate an authentic Odoo schema export that contains sales, product, partner, user, company, currency, stock, purchase, and accounting metadata.
- [ ] Parse it without replacing the current default until evaluation passes.
- [ ] Compare latency, hallucination, over-selection, and relationship validity against focused and expanded fixtures.
- [ ] Adopt a larger default schema only after tests and evaluation support it.

### Step 7 - Dense Retrieval Decision

- [x] Keep dense retrieval disabled by default.
- [ ] Evaluate dense retrieval only after the authentic larger schema exists.
- [ ] Adopt dense retrieval only if it improves recall without increasing hallucination or unacceptable latency.

## Newly Implemented Behavior

- Arabic typo handling now uses conservative `rapidfuzz` matching against configured aliases only.
- Debug understanding can include `matched_terms` with input token, matched alias, target entity, score and match type.
- Projection responses now include additive fields: `supported` and `unsupported_reason`.
- Out-of-domain questions return HTTP `200 OK` with `supported=false`, `models=[]`, and `schema={}`.
- The pipeline no longer falls back to `sale.order` or the first schema model for unsupported questions.
## Latest V2 Hardening Update

- Broader Arabic role detection is covered by tests and expanded golden cases.
- Ambiguous person-only queries such as `اعطني معلومات احمد` expose `ambiguities` in debug and remain unsupported instead of selecting a schema branch.
- Budget and negative path cases are tested for low depth and total-field limits.
- Mapper fidelity review is documented: inferred reverse relation names are synthetic, e.g. `sale_order_line_ids`, and are not claimed to match every real Odoo field name such as `order_line`.
- `app.schema.authenticity` can evaluate whether a supplied SQL schema is ready for authentic Odoo scale testing.
- Dense retrieval remains disabled by default until an authentic larger schema exists.
## Runtime Commands

Focused runtime:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Expanded runtime:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.expanded:app --host 127.0.0.1 --port 8002 --reload
```

Default evaluation:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner
```

Expanded evaluation:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --expanded
```

Tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Assumptions And Decisions

- This phase is backend-only. No project UI is planned.
- Swagger `/docs` is FastAPI's built-in API documentation, not a custom UI.
- The backend returns schema metadata, not real sales records.
- The backend does not execute SQL from user queries.
- The backend does not connect to an operational ERP database.
- The backend does not generate Odoo domains yet.
- `data/raw/odoo/schema.sql` remains the focused default source.
- `data/raw/odoo/schema.expanded.sql` is opt-in and synthetic.
- `.agents/PLAN.md` is the only accepted plan source.
- Details of the five reviewed repositories are not documented in this repo, so this plan records general lessons only.
