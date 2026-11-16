# Layering

```
api (routers, deps)  →  services  →  repositories  →  models
        ↓                  ↓
     schemas            core (errors, clock, config)
```

Imports flow only in the direction of the arrows. `models` import nothing from the app except `core.database`.

## Rules

- **Routers** (`src/message_router/api/*.py`): declare the route, parse/validate input through schemas, call exactly one service
  method, return its result. No `if` on business state, no `select(...)`, no `session.commit()`.
- **Services** (`src/message_router/services/*.py`): classes taking a `Session` (or repositories) in `__init__`; own business
  rules, status transitions, and the transaction (commit once at the end of a mutating method). Raise domain
  exceptions. Return ORM objects; the router's `response_model` serialises them.
- **Repositories** (`src/message_router/repositories/*.py`): `select`/`add`/`flush` only. Return entities or `None`; the service
  decides whether `None` means 404. No rules, no commits.
- **Pure logic** (e.g. `services/classifier.py`): plain functions with no I/O, so they unit-test without a DB.
- Dependencies are wired in `src/message_router/api/deps.py` with `Annotated[..., Depends(...)]` type aliases
  (`DbSession`, `MessageServiceDep`) — routers never instantiate services.

## Review checks

- LAY-01: a router contains no query, commit, or business conditional.
- LAY-02: a service never imports `fastapi` (no `HTTPException`, no `Depends`).
- LAY-03: a repository never commits and never raises domain exceptions.
- LAY-04: no module imports "upward" (repositories importing services, models importing schemas).
