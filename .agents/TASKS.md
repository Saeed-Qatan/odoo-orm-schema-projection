# Tasks

## Current Task

### Title
Implement V3 Structured ORM Metadata JSON Source

### Status
DONE

Allowed:

- TODO
- IN_PROGRESS
- BLOCKED
- REVIEW
- DONE

### Goal

Create branch `v3` from the stable `v2` state and add a structured Odoo ORM metadata JSON source path that can feed the existing projection pipeline without changing public API behavior.

### Scope

Expected modules/files:

- `app/schema/models.py`
- `app/schema/adapters/orm_metadata_json_adapter.py`
- `app/schema/authenticity.py`
- `app/evaluation/metadata_golden_set.py`
- `app/evaluation/runner.py`
- `data/raw/odoo/orm_metadata.sample.json`
- `tests/test_orm_metadata_json_adapter.py`
- `tests/test_metadata_evaluation.py`
- `tests/test_schema_authenticity.py`
- `.agents/PLAN.md`
- `.agents/CURRENT_STATE.md`
- `.agents/TASKS.md`
- `README.md`

### Do Not Change

- existing endpoint names
- existing route methods
- default runtime schema source
- Odoo runtime integration
- Odoo domain generation
- dense retrieval default behavior
- production databases or external services

### Requirements

- Keep the project disconnected from live Odoo; current sources are local SQL/JSON files only.
- JSON metadata adapter must convert modules to the existing `OrmSchema` contract.
- Adapter must preserve descriptions, keywords, common domains, field groups, choices, and relation metadata.
- Relation fields must remain projectable by the existing graph/pipeline path.
- Readiness checker must support SQL and metadata JSON sources.
- Sample metadata must not be reported as an authentic Odoo schema candidate.
- Existing API behavior must remain unchanged.

### Acceptance Criteria

The task is complete when:

- metadata JSON adapter tests pass.
- metadata projection/evaluation tests pass.
- schema authenticity tests pass for SQL and JSON sources.
- default and expanded evaluation still pass.
- full pytest passes.
- documentation describes the V3 behavior and limits.

### Verification

Executed successfully:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_orm_metadata_json_adapter.py tests/test_metadata_evaluation.py tests/test_schema_authenticity.py tests/test_projection.py
# 25 passed

.\.venv\Scripts\python.exe -m pytest
# 57 passed, 2 warnings

.\.venv\Scripts\python.exe -m app.evaluation.runner
# 20 cases, precision/recall 1.0, hallucination/over-selection/failed paths 0

.\.venv\Scripts\python.exe -m app.evaluation.runner --expanded
# 16 cases, precision/recall 1.0, hallucination/over-selection/failed paths 0

.\.venv\Scripts\python.exe -m app.evaluation.runner --metadata-json
# 3 cases, precision/recall 1.0, hallucination/over-selection/failed paths 0

.\.venv\Scripts\python.exe -m app.schema.authenticity data/raw/odoo/orm_metadata.sample.json
# source_kind=orm_metadata_json, sample_marker_found=true, is_authentic_candidate=false, is_scale_ready=false
```

### Notes

No public endpoint was added in this step. `POST /api/v1/schema/inspect-source` remains optional future work if source readiness needs to be exposed over HTTP.

The project still has no live Odoo connection. V3 prepares the backend to consume a structured local metadata export later, after a real export exists.
