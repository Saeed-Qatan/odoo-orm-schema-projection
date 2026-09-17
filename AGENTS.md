# Agent Instructions

This repository is a Python backend project.

The repository and the documentation under `.agents/` are the source of truth.

Do not start non-trivial implementation before understanding the relevant
architecture, existing code, current project state, and task scope.

---

# Required Reading

Before any non-trivial task, read:

- `.agents/PROJECT.md`
- `.agents/ARCHITECTURE.md`
- `.agents/RULES.md`
- `.agents/CURRENT_STATE.md`
- `.agents/PLAN.md`

For implementation tasks also read:

- `.agents/TASKS.md`

Do not load irrelevant documents unnecessarily.

---

# Mandatory Workflow

For every non-trivial change:

Understand
-> Inspect
-> Plan
-> Implement
-> Test
-> Review
-> Verify

Never skip directly from request to implementation.

---

# Repository First

Before modifying existing behavior:

1. Search the repository.
2. Locate the relevant implementation.
3. Read related modules.
4. Inspect related tests.
5. Inspect dependencies and interfaces.
6. Understand the current behavior.
7. Only then modify code.

Never assume that a file, function, model, endpoint, database table,
configuration option, dependency, or business rule exists.

---

# Evidence Levels

Clearly distinguish between:

OBSERVED
Verified directly from repository code, configuration, tests, or documentation.

INFERRED
Likely based on available evidence but not explicitly verified.

PROPOSED
A new recommendation or implementation idea.

Never present INFERRED or PROPOSED information as OBSERVED fact.

---

# Architecture

Follow:

`.agents/ARCHITECTURE.md`

Do not bypass architectural layers for convenience.

Do not introduce a new architectural pattern without a clear reason.

Architectural changes must be documented in:

`.agents/CURRENT_STATE.md`

---

# Scope Control

Implement the smallest coherent solution that satisfies the task.

Do not:

- refactor unrelated code
- rename unrelated files
- redesign unrelated modules
- add speculative abstractions
- implement future features
- add dependencies without justification

---

# Verification

Never claim:

- fixed
- completed
- working
- tested
- production ready
- all tests pass

unless the corresponding verification was actually executed successfully.

If verification could not be completed, explicitly say:

NOT VERIFIED

and explain what was not verified.

---

# Security

Never expose or commit:

- passwords
- access tokens
- API keys
- ERP credentials
- database passwords
- private keys
- production secrets

Never weaken authentication, authorization, validation, or tenant isolation
to make a feature work.

---

# Destructive Operations

Do not automatically execute:

- DROP
- TRUNCATE
- destructive migrations
- mass DELETE
- production data changes
- irreversible operations

without explicit authorization.

---

# Documentation Synchronization

If implementation changes:

- architecture
- API contracts
- database structure
- security rules
- major project behavior

update the relevant `.agents/` documentation.

If documentation and implementation contradict each other,
do not silently choose one.

Identify the contradiction and determine which represents the intended state.

---

# Final Check

Before considering the task complete, follow:

`.agents/TASKS.md`



