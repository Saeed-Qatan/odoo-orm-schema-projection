# Current State

## Status

The project is in V2 expansion hardening.

The latest completed backend task is the opt-in expanded API runtime with source-isolated schema caches. The latest documentation task synchronized the official project plan with the V2 progress that has already been committed and pushed.

## Branch

Current active development branch:

```text
v2
```

Remote branch `origin/v2` contains the expanded runtime and schema work.

## Documentation Structure

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

## V2 Expanded Runtime State

- Active branch: `v2`.
- `app.main:app` keeps the focused default fixture.
- `app.expanded:app` opts into `data/raw/odoo/schema.expanded.sql` with separate expanded ORM, graph and index paths.
- `app.application.create_app(settings)` builds each runtime with one explicit settings instance.
- Repository cache metadata validates source identity/content, aliases/parser/mapper/model code and artifact integrity.
- `schema.expanded.sql` is synthetic: it preserves the larger source and appends sales/product metadata for development testing. It is not a genuine Odoo sales export.

## Historical Verification Snapshot

Latest verified checks from the V2 work:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m app.evaluation.runner
.\.venv\Scripts\python.exe -m app.evaluation.runner --expanded
```

Observed historical results:

- Full `pytest`: 36 passed, with 2 dependency deprecation warnings.
- Focused evaluation: 20 cases, precision/recall 1.0, relationship validity 1.0, hallucination/over-selection/failed paths 0.
- Expanded evaluation: 14 cases, precision/recall 1.0, relationship validity 1.0, hallucination/over-selection/failed paths 0.
- Live expanded runtime on `127.0.0.1:8002`: health ok, 173 models, Arabic customer/country and salesperson role projection verified over HTTP.

Re-run checks before claiming a new current verification snapshot.

## Current Plan

The synchronized plan marks the following as done:

- Foundation, parser, ORM mapper, graph, retrieval, query projection pipeline and API.
- Request protection, timeout/rate-limit tests and evaluation reports.
- Codex instruction layer.
- V1/V2 branch work and V2 push.
- Opt-in expanded runtime and source-isolated cache behavior.

Remaining work is grouped under:

- Arabic query understanding expansion.
- Ambiguity handling.
- Budget and negative-case coverage.
- Mapper fidelity review.
- Authentic Odoo sales schema acquisition and validation.
- Dense retrieval decision after a larger authentic schema exists.

## Arabic Typo And Out-of-Domain Guard

- Added conservative fuzzy alias matching with `rapidfuzz` inside query understanding.
- Fuzzy matching is restricted to configured aliases and records matched terms in debug metadata.
- Single-word aliases now match full tokens only; phrase aliases may match within the normalized query.
- Projection responses now include additive fields: `supported` and `unsupported_reason`.
- Out-of-domain questions such as `ماهي تكنولوجيا المعلومات` return `supported=false`, `models=[]`, and `schema={}` with HTTP `200 OK`.
- Ambiguous person-only questions such as `اعطني معلومات احمد` no longer fallback to `sale.order` without a sales/customer/salesperson context.
- Targeted verification passed: 26 tests in `tests/test_query_understanding.py`, `tests/test_projection.py`, and `tests/test_api.py`.
- Full verification after this change: targeted tests 26 passed, full pytest 42 passed, expanded evaluation 14 cases with precision/recall 1.0, hallucination/over-selection/failed paths 0, p95 26.28ms.
## V2 Remaining-Plan Hardening

- Broader Arabic role detection is covered for salesperson, customer, country/region, company/branch, currency, category, product, quantity, status, total and date aliases.
- Query understanding now exposes `ambiguities` for person-like filters without enough context, such as `احمد` in `اعطني معلومات احمد`.
- Ambiguous person-only questions remain unsupported and do not select a schema branch.
- Expanded budget and negative-path behavior is tested for low depth and total-field limits.
- Expanded golden set now includes 16 cases and covers typo and combined Arabic role queries. Latest expanded evaluation: precision/recall 1.0, hallucination/over-selection/failed paths 0, p95 23.402ms.
- Mapper fidelity review is documented: inferred reverse relation names are synthetic and validated by tests, but not claimed to match every real Odoo field name.
- Added `app.schema.authenticity` to evaluate whether a supplied SQL source is an authentic Odoo scale candidate.
- Current local sources are not authentic Odoo sales exports. Authentic Odoo schema adoption remains blocked until the user provides or generates a real export.
- Dense retrieval remains disabled by default and is not adopted until authentic large-schema evaluation justifies it. Latest full pytest: 51 passed, 2 warnings.
