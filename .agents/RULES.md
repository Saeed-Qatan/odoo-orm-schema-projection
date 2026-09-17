# Engineering Rules

## Repository First

Inspect existing code before making assumptions.

Search for existing patterns before creating new ones.

Never invent repository behavior.

## No Sycophancy

Do not agree with a technical suggestion only because the user proposed it.

Evaluate it based on:

- correctness
- security
- maintainability
- architecture
- complexity
- performance

If there is a better solution, explain it clearly.

## Scope

Make the smallest coherent change required.

Do not:

- refactor unrelated code
- rename unrelated files
- redesign working modules
- implement future features
- add unnecessary abstractions

## Python

Use:

- type hints
- clear naming
- small focused functions
- explicit behavior
- meaningful exceptions

Avoid:

- global mutable state
- unnecessary metaprogramming
- circular dependencies
- deeply nested logic
- excessive abstraction

## FastAPI

Keep routers thin.

Business logic belongs in services.

Database access belongs in repositories or dedicated persistence modules.

Use Pydantic for request and response validation.

## Database

Use migrations for schema changes.

Use parameterized queries.

Consider:

- indexes
- foreign keys
- constraints
- transactions
- query performance

Do not perform destructive database operations without explicit approval.

## Security

Never expose:

- passwords
- tokens
- API keys
- private keys
- database credentials

Never weaken authentication, authorization, or validation just to make code work.

Treat all external input as untrusted.

## Dependencies

Before adding a dependency:

1. Check existing dependencies.
2. Check whether Python already provides the required functionality.
3. Confirm the dependency is actually necessary.

Avoid unnecessary packages.

## Error Handling

Never silently swallow exceptions.

Do not use:

```python
except:
    pass
```

Handle expected failures intentionally.

Unexpected failures must remain observable.

## Verification

Never say:

- fixed
- working
- complete
- tests pass

unless verified.

If verification was not performed, state:

NOT VERIFIED

## Overengineering

Do not introduce:

- microservices
- event buses
- factories
- plugin systems
- abstract interfaces
- caching layers
- distributed systems

unless the current problem actually requires them.

Prefer the simplest design that solves the real requirement.
