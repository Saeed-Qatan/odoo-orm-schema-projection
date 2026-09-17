# Current State

## Status

The project is back in backend implementation work after organizing the
repository-local agent instruction layer.

The latest completed development task is backend protection and limits hardening.

## Branch

Current active development branch:

```text
develop
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

