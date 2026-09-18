# Tasks

## Current Task

### Title
Opt-In Expanded API Runtime And Source-Isolated Caches

### Status
DONE

### Goal
Allow expanded-fixture API testing without replacing the focused runtime or reusing ORM caches from a different source.

### Scope
- app/application.py
- app/expanded.py
- app/main.py
- app/app_state.py
- app/api/routes/projection.py
- app/api/routes/schema.py
- app/schema/repository.py
- tests/test_api.py
- tests/test_schema_repository.py
- .gitignore
- README and relevant .agents documentation
- generated source-specific ORM/graph artifacts

### Do Not Change
- endpoint names and response contracts
- default schema source
- production databases
- unrelated application behavior

### Requirements And Acceptance Criteria
- Construct app/pipeline/routers with one explicit settings instance.
- Keep expanded source artifacts separate from focused artifacts.
- Cache validity must depend on source identity/content, parser/mapper/models/aliases and artifact integrity.
- Test cache reuse, source switching and content changes with unchanged timestamps.
- Verify schema/model endpoints and Arabic/product projection over the expanded API.

### Verification
- Full pytest: 36 passed, 2 dependency deprecation warnings, 7.22s.
- Live 8002 health: ok; model count: 173.
- Live Arabic role projection: correct separate customer/country and salesperson branches, zero hallucination; pipeline latency 30.437ms.
- Existing 8001 server left running.

### Notes
Expanded source is still synthetic. Current changes are not committed or pushed. Next: broader Arabic ambiguity, budget coverage and mapper fidelity review before default adoption or authentic Odoo integration.
