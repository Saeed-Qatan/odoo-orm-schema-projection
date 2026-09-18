# Tasks

## Current Task

### Title
Arabic Typo Understanding And Out-of-Domain Guard

### Status
DONE

Allowed:

- TODO
- IN_PROGRESS
- BLOCKED
- REVIEW
- DONE

### Goal

Improve deterministic Arabic query understanding for light spelling mistakes and prevent unrelated user questions from projecting arbitrary schema.

### Scope

Expected modules/files:

- `app/projection/query_understanding.py`
- `app/projection/pipeline.py`
- `app/schema/models.py`
- `data/config/schema_aliases.json`
- `tests/test_query_understanding.py`
- `tests/test_projection.py`
- `tests/test_api.py`
- `.agents/PLAN.md`
- `.agents/CURRENT_STATE.md`
- `.agents/TASKS.md`

### Do Not Change

- endpoint names
- HTTP method or route paths
- database/schema source files
- dense retrieval defaults
- production databases
- unrelated application behavior

### Requirements

- Use existing `rapidfuzz`; do not add new dependencies.
- Match light Arabic spelling mistakes against configured aliases only.
- Record fuzzy alias matches in debug metadata.
- Return `200 OK` with `supported=false` and empty schema for out-of-domain questions.
- Do not fallback to `sale.order` or the first schema model for unrelated questions.
- Preserve existing golden-set behavior and avoid over-selection.

### Acceptance Criteria

The task is complete when:

- `المندو` is recognized as `salesperson_name` through fuzzy matching.
- `ماهي تكنولوجيا المعلومات` returns `supported=false`, `models=[]`, and `schema={}`.
- `اعطني معلومات احمد` does not select sales schema without sales/customer/salesperson context.
- Existing focused and expanded projection tests remain green.
- API response remains backward compatible through additive fields.

### Verification

Executed successfully:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_query_understanding.py tests\test_projection.py tests\test_api.py
# 26 passed, 2 warnings

.\.venv\Scripts\python.exe -m pytest
# 42 passed, 2 warnings

.\.venv\Scripts\python.exe -m app.evaluation.runner --expanded
# 14 cases, precision/recall 1.0, hallucination/over-selection/failed paths 0
```

### Notes

This change intentionally keeps fuzzy matching conservative. Single-word aliases must match full tokens; substring matching is allowed only for phrase aliases. This prevents false positives such as matching `المنتج` inside `المنتجات` when the expected projection only asks for quantity.
