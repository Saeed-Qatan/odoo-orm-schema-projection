# Tasks

## Current Task

### Title
Complete V2 Hardening Backlog Where Locally Feasible

### Status
DONE

Allowed:

- TODO
- IN_PROGRESS
- BLOCKED
- REVIEW
- DONE

### Goal

Complete the remaining locally feasible V2 backlog: broader Arabic role detection, ambiguity debug behavior, budget/negative-case coverage, mapper fidelity documentation/tests, authentic-schema readiness checks, and dense retrieval decision guardrails.

### Scope

Expected modules/files:

- `app/projection/query_understanding.py`
- `app/projection/pipeline.py`
- `app/schema/models.py`
- `app/schema/authenticity.py`
- `data/config/schema_aliases.json`
- `app/evaluation/expanded_golden_set.py`
- `tests/test_query_understanding.py`
- `tests/test_projection.py`
- `tests/test_orm_mapper.py`
- `tests/test_schema_authenticity.py`
- project documentation under `.agents/` and README

### Do Not Change

- endpoint names
- route methods
- default schema source
- dense retrieval default
- production databases
- unrelated application behavior

### Requirements

- Keep schema selection deterministic.
- Expose ambiguity in debug without hallucinating models.
- Keep unsupported and ambiguous non-domain queries as empty projections.
- Test budget and incomplete-path behavior.
- Document synthetic mapper/source limitations.
- Add authentic-schema readiness checks without claiming current fixtures are authentic.
- Keep dense retrieval disabled by default.

### Acceptance Criteria

The task is complete when:

- Broader Arabic roles are detected and evaluated.
- Ambiguous person-only filters produce debug ambiguity and no schema branch.
- Low-depth and low-total-field limits preserve valid output/debug consistency.
- Mapper fidelity gaps are documented and covered by tests.
- Synthetic sources are reported as not authentic Odoo scale candidates.
- Expanded evaluation remains precise with zero hallucination and over-selection.

### Verification

Executed successfully:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_query_understanding.py tests\test_projection.py tests\test_orm_mapper.py tests\test_schema_authenticity.py
# 28 passed

.\.venv\Scripts\python.exe -m app.evaluation.runner --expanded
# 16 cases, precision/recall 1.0, hallucination/over-selection/failed paths 0

.\.venv\Scripts\python.exe -m app.schema.authenticity data/raw/odoo/schema.expanded.sql
# is_authentic_candidate=false, synthetic_marker_found=true, missing scale models: account.move, purchase.order, stock.picking

.\.venv\Scripts\python.exe -m pytest
# 51 passed, 2 warnings
```

### Notes

Authentic Odoo schema adoption is not complete because no genuine Odoo sales-enabled SQL export exists in the repository. The added readiness checker tells us when a supplied schema is suitable for the next phase.
