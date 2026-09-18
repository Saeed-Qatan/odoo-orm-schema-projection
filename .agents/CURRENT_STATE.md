# Current State

## Status

The project is back in backend implementation work after organizing the
repository-local agent instruction layer.

The latest completed development task is backend protection and limits hardening.

## Branch

Current active development branch:

```text
v2
```

## Backend Prototype State

The backend prototype has been stabilized with:

- FastAPI API endpoints.
- Query understanding driven by `data/config/schema_aliases.json`.
- PostgreSQL schema parsing with `pglast` and regex fallback.
- ORM-like schema mapping.
- NetworkX relationship graph traversal.
- Query-guided traversal guard.
- Field-level pruning.
- Golden-set evaluation with `app.evaluation.runner`.
- In-memory rate limiting on projection and schema read endpoints.
- Projection request timeout handling that returns `504`.
- Request/query and budget limit tests.

## Verification Snapshot

Latest successful checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api.py tests\test_projection.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m app.evaluation.runner
```

Observed latest results:

- Targeted tests: 8 passed.
- Full `pytest`: 18 passed.
- Evaluation cases: 20.
- Model precision/recall average: 1.0 / 1.0.
- Field precision/recall average: 1.0 / 1.0.
- Relationship validity average: 1.0.
- Hallucination count: 0.
- Over-selection count: 0.
- Failed path count: 0.
- P95 latency: 1.005ms.

## Current Documentation Structure

Keep this instruction structure:

```text
AGENTS.md
.agents/
├── PROJECT.md
├── ARCHITECTURE.md
├── RULES.md
├── CURRENT_STATE.md
├── TASKS.md
└── PLAN.md
```

Removed from intended structure:

- `.agents/specs/`
- `.agents/skills/`
- nested `.agents/core/`
- nested `.agents/workflow/`

## Plan Source

The repository-local plan source for agent context is:

```text
.agents/PLAN.md
```

The root `plan.md` has been removed. Agents must use `.agents/PLAN.md` as the only project plan source when preparing non-trivial project work.


## V2 Parser Progress

- Active branch: `v2`; the previous verified snapshot is saved on remote `v1`.
- Fixed pglast ALTER TABLE handling to ignore non-constraint payloads.
- Added ALTER TABLE primary-key extraction and inherited-column resolution.
- Verified full source directly through pglast: 168 tables, 1671 columns including inherited columns, 516 foreign keys, 131 tables with primary keys.
- All extracted foreign-key endpoints passed validation.
- Verification: parser tests 4 passed; full suite 20 passed (2 dependency deprecation warnings).
- Default runtime source remains the focused sample. The full source has no sales/product tables.
- Remaining: regex fallback primary keys, inheritance and statement-boundary correctness; larger sales-capable source; ORM mapping scale checks.

## V2 Fallback Verification

- Regex fallback now extracts ALTER primary keys, resolves inherited columns, and does not carry FOREIGN KEY matching across semicolon statement boundaries.
- Fixed accidental rejection of the checksum column by constraint-prefix matching.
- Full-source comparison passed for table names, column names, nullability, primary-key flags and foreign-key endpoints. Type normalization and arbitrary PostgreSQL syntax equivalence are not claimed.
- Parser tests: 6 passed. Full suite: 22 passed, 2 dependency deprecation warnings.
- Current sample evaluation: 20 cases, model/field precision and recall 1.0, relationship validity 1.0, hallucination/over-selection/failed paths 0; p95 1.656ms.
- Next task: prepare a larger sales-capable schema and verify ORM mapping. Default source remains unchanged.

## V2 Expanded Fixture

- Created `data/raw/odoo/schema.expanded.sql` from the unchanged full source plus five synthetic sales/product tables, not a genuine Odoo export.
- Verified parser and ORM mapping: 173 tables/models, 1699 raw columns, 525 foreign keys; all FK endpoints valid.
- Added test coverage for salesperson/company/currency and product-template/category links, inferred sales lines, and fallback relationship parity.
- Added regex support for column-level REFERENCES discovered by the new fixture test.
- Parser tests: 7 passed. Default API source remains the focused sample.
- Query understanding and golden expectations still target the old product-name location. Expanded API projection is NOT VERIFIED and must not be adopted as default yet.

Latest full verification: 23 tests passed, with 2 dependency deprecation warnings.
This run took 206.15 seconds; the cause of the unusually long duration was not investigated. This is test-suite wall time, not projection request latency.

## V2 Schema-Aware Product Projection

- QueryUnderstandingExtractor now receives the schema from the pipeline and selects configured schema_variants only when all required fields exist.
- Product configuration resolves names through product.product.product_tmpl_id -> product.template.name on the expanded fixture, while the focused sample retains product.product.name.
- Expanded golden set: 6 cases, including the original Arabic demo question.
- Expanded report: data/processed/evaluation_report.expanded.json. Model and field precision/recall 1.0, relationship validity 1.0, hallucination and over-selection 0; p95 22.342ms on this local run.
- Verification: full suite 26 passed (3.99s, 2 dependency deprecation warnings); after adding the Arabic case, projection tests 5 passed.
- Default API source is unchanged. Expanded projection is verified only for these six cases. Country/state/company/currency/category and explicit salesperson-name understanding remain future work.

## V2 Role-Scoped Projection (Latest)

- Active branch: v2.
- Added sales-context Arabic/English paths for customer country/region, order company/currency, product category and salesperson name.
- QueryUnderstanding.field_paths is additive debug metadata. Every hop is validated against the active schema.
- Projection keeps each relation occurrence separate: salesperson partner fields do not inherit customer geography fields.
- Relation depth is enforced per path. Category requires max_depth=4. Incomplete paths are removed after budget pruning; models/metrics/debug paths match emitted selections.
- Expanded evaluation: 14 cases; model/field precision and recall 1.0; relationship validity 1.0; hallucination/over-selection/failed paths 0; p95 26.69ms.
- Focused evaluation: 20 cases; precision/recall 1.0, zero hallucination/over-selection/failed paths (regression tested).
- Full tests: 31 passed, 2 dependency deprecation warnings, 5.76s.
- Command: python -m app.evaluation.runner --expanded. Builds metadata in memory without overwriting focused caches.
- Default API source remains schema.sql. Arbitrary language ambiguity is not resolved; Ahmed still follows the existing salesperson filter rule.
- Next: opt-in expanded API runtime with source-specific caches and integration tests, then broader Arabic coverage before default adoption.

## V2 Expanded API Runtime (Latest)

- Added app.application.create_app(settings) so each app builds its pipeline and routers with the same explicit settings.
- app.main:app keeps the default fixture. app.expanded:app opts into schema.expanded.sql, .expanded.json ORM/graph files and data/indexes/expanded.
- Repository cache metadata now validates source identity and content hashes, including SQL/parser/mapper/models/aliases and the artifact. Ignored local .metadata.json files prevent source switching from accidentally reusing another schema.
- Graph write failures are logged instead of silently discarded.
- Verified full pytest: 36 passed, 2 dependency deprecation warnings, 7.22s.
- Live expanded server started on 127.0.0.1:8002. Health returned ok, model list returned 173, and Arabic customer/country/salesperson HTTP request returned correct separate branches, zero hallucination and 30.437ms pipeline latency.
- Existing server on 8001 was left running. The server on 8002 was started without auto-reload; README includes a reload command for manual development runs.
- Current V2 changes remain local/uncommitted. Next: expand Arabic/ambiguous-query and budget coverage, review remaining mapper scale limitations, and obtain an authentic sales-enabled Odoo export before claiming genuine ORM fidelity.
