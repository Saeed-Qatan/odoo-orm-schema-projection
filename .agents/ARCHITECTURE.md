# Architecture

Use a clear layered architecture.

Recommended flow:

```text
Request
↓
FastAPI Router
↓
Service / Use Case
↓
Repository / Integration
↓
Database / External Service
```

For this project, the current practical flow is:

```text
HTTP Request
↓
app/api/routes/*
↓
app/projection/pipeline.py
↓
app/projection/* + app/retrieval/* + app/graph/*
↓
app/schema/repository.py + app/schema/adapters/*
↓
data/raw + data/processed + data/config
```

## API Layer

Responsible for:

- HTTP requests
- input validation
- dependency injection
- response serialization
- HTTP status codes

Keep routers thin.

Do not place core business logic inside routers.

Current API modules:

- `app/api/routes/health.py`
- `app/api/routes/schema.py`
- `app/api/routes/projection.py`

Routers should call the pipeline or application services and return typed
responses. They should not perform schema linking, graph traversal, pruning, or
evaluation logic directly.

## Service / Use Case Layer

Responsible for:

- business logic
- use cases
- workflow coordination
- validation between components

Services should not depend on HTTP-specific concepts.

In this project, the primary use-case coordinator is:

- `app/projection/pipeline.py`

The projection pipeline coordinates:

- query understanding
- retrieval
- schema linking
- graph traversal
- pruning
- validation
- hierarchical schema projection

The pipeline may depend on domain-oriented components, but should not depend on
FastAPI request or response objects.

## Projection Components

Projection components live in:

- `app/projection/`

Responsibilities:

- interpret user query intent and entities
- link query concepts to schema models and fields
- enforce query-guided traversal boundaries
- prune unnecessary fields
- build hierarchical output

Do not move projection rules into routers or schema adapters.

## Retrieval Components

Retrieval components live in:

- `app/retrieval/`

Responsibilities:

- build searchable schema corpus
- run BM25 retrieval
- run fuzzy matching
- optionally run dense retrieval
- merge candidates with RRF

Retrieval can suggest candidates, but it must not bypass strict validation or
query-guided traversal rules.

## Graph Components

Graph components live in:

- `app/graph/`

Responsibilities:

- represent models, fields, and relationships as a graph
- find valid relationship paths
- expose traversal helpers

Graph traversal must use relationships from the ORM-like schema only. It must
not invent model or field relationships.

## Repository Layer

Responsible for:

- persistence
- data retrieval
- loading and saving generated schema artifacts

Avoid direct database or filesystem persistence access from routers.

Current repository module:

- `app/schema/repository.py`

Current storage is file-based, not database-backed:

- `data/raw/odoo/schema.sql`
- `data/processed/odoo_orm_schema.json`
- `data/processed/odoo_schema_graph.json`
- `data/processed/evaluation_report.json`
- `data/config/schema_aliases.json`

## Schema Adapters

Schema adapters live in:

- `app/schema/adapters/`

Responsibilities:

- parse external schema sources
- convert them into raw internal schema models

Current adapter:

- `PostgresSqlSchemaAdapter`

It should parse PostgreSQL schema metadata only. It must not perform query
understanding, projection, or API response shaping.

## Integrations

External services must be isolated behind dedicated modules or clients.

Do not spread third-party API logic across the application.

Current third-party/library integrations include:

- `pglast` in schema parsing
- `networkx` in graph building/traversal
- `rank-bm25` in retrieval
- `rapidfuzz` in fuzzy retrieval
- optional `sentence-transformers` and `faiss-cpu` in dense retrieval

Keep integration-specific code inside the module that owns that concern.

## Evaluation Layer

Evaluation code lives in:

- `app/evaluation/`

Responsibilities:

- define golden queries
- evaluate projection quality
- summarize metrics
- write evaluation reports

Evaluation must not change production request behavior.

## Dependency Direction

Higher-level business logic should not depend unnecessarily on infrastructure
details.

Keep modules loosely coupled.

Preferred direction:

```text
api -> projection pipeline -> projection/retrieval/graph/schema services -> repository/adapters/files
```

Avoid reverse dependencies such as:

- schema adapters importing FastAPI routers
- retrieval modules importing API routes
- graph modules depending on HTTP concepts
- routers performing parser or traversal internals

## Architecture Changes

Before introducing a new architectural pattern:

1. Check whether the existing architecture already solves the problem.
2. Explain why the change is necessary.
3. Consider simpler alternatives.
4. Avoid rewriting unrelated components.

Architectural decisions that change layering, data flow, major module
responsibilities, or public contracts must be documented in:

```text
.agents/CURRENT_STATE.md
```


## Explicit Query Relationship Paths

Sales aliases may define field_paths: the root model followed by exact field names.
Understanding validates every hop against the active schema. The pipeline enforces
relation depth and the projector scopes children to each relationship occurrence,
preventing shared model fields from leaking between customer and salesperson roles.
Incomplete paths are removed after budget pruning. Queries without explicit paths
retain legacy graph traversal. Default schema/cache changes are separate work.

## Application Construction And Source-Isolated Caches

app.application.create_app(settings) builds each application using one explicit
Settings instance for its pipeline and routers. app.main retains the default
runtime; app.expanded provides an opt-in synthetic expanded runtime with separate
ORM/graph/index paths. This factory exists to make source-isolated API integration
tests and parallel local runtime instances possible.

SchemaRepository keeps ORM payload shape unchanged and records source/content
and artifact hashes in a local metadata sidecar. Old or mismatched caches are
rebuilt; sidecars are not committed. Graph snapshots are regenerated from the
active schema during application construction. Graph save failures are logged.
