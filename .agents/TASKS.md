# Tasks

## Current Task

### Title

Backend Protection And Limits Hardening

### Status

DONE

Allowed:

- TODO
- IN_PROGRESS
- BLOCKED
- REVIEW
- DONE

### Goal

Stabilize backend protection behavior for the schema projection API by verifying
rate limits, request timeout handling, query length validation, and budget limit
clamping with focused tests.

### Scope

Expected modules/files:

- `app/api/routes/projection.py`
- `tests/test_api.py`
- `tests/test_projection.py`
- `.agents/PLAN.md`
- `.agents/CURRENT_STATE.md`
- `.agents/TASKS.md`

### Do Not Change

- public endpoint names
- successful API response shape
- schema source files
- projection selection behavior unrelated to protection
- generated schema/graph artifacts unless evaluation regenerates reports

### Requirements

- Keep routers thin.
- Return `429` when projection or schema read rate limits are exceeded.
- Return `504` when projection execution exceeds `request_timeout_ms`.
- Keep query length validation active.
- Keep budget clamping for oversized projection options.
- Do not add new dependencies.

### Acceptance Criteria

The task is complete when:

- projection rate limit is covered by a test.
- schema read rate limit is covered by a test.
- projection timeout is covered by a test.
- query length validation is covered by a test.
- budget clamping is covered by a test.
- full tests pass.
- evaluation remains clean with zero hallucination and zero over-selection.

### Verification

Executed successfully:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_api.py tests\test_projection.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m app.evaluation.runner
```

Observed results:

- Targeted tests: 8 passed.
- Full `pytest`: 18 passed.
- Evaluation cases: 20.
- Hallucination count: 0.
- Over-selection count: 0.
- Relationship validity average: 1.0.

### Notes

- `app/api/routes/projection.py` now catches both `TimeoutError` and `asyncio.TimeoutError` for projection timeout handling.
- `tests/test_api.py` covers query length, projection rate limit, schema read rate limit, and timeout behavior.
- `tests/test_projection.py` covers budget clamping for oversized options.


