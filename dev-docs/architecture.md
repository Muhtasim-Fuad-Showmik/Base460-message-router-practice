# Architecture

## Layout

```
src/message_router/
  main.py            # app factory: routers, exception handlers, lifespan (create tables)
  api/               # routers + FastAPI dependencies (deps.py). Thin: parse → call service → return schema
    deps.py          # get_db (session per request), service providers
    properties.py
    messages.py
  core/
    config.py        # settings (DB URL) — env-overridable, SQLite default
    database.py      # engine, SessionLocal, Base
    errors.py        # domain exceptions + handlers (RFC 9457 problem+json)
    clock.py         # utcnow() — single seam for time
  models/            # SQLAlchemy ORM entities + enums
  schemas/           # Pydantic: *Create, *Response, *Filter, list/page wrappers
  services/          # business rules, status transitions, transaction boundary
    classifier.py    # pure function: content -> MessageIntent (no I/O)
  repositories/      # queries only (select/insert), no business rules
tests/
  unit/              # pure logic: classifier, state transitions
  integration/       # HTTP via TestClient against in-memory SQLite
```

Enums (`Channel`, `MessageIntent`, `MessageStatus`, `ResponseType`) live in `src/message_router/models/enums.py` and are reused by
the schemas — one definition, no duplicated string literals.

## Design patterns — chosen

| Pattern | Where | Why |
|---|---|---|
| Layered architecture (router → service → repository) | whole app | Keeps routers thin and rules testable |
| Dependency Injection via `Depends` | `api/deps.py` | `Session` per request, services built from the session; tests override `get_db` |
| Repository | `repositories/` | Isolates SQLAlchemy queries (filters + pagination) from rules; one place to fix N+1 |
| DTO / schema separation | `schemas/` vs `models/` | Request, response and persistence shapes evolve independently; `response_model` filters output |
| Strategy as ordered data | `services/classifier.py` | Classification is an ordered list of `(intent, keywords)` rules; first match wins; adding a rule is a data change, not a code branch. Pure function → trivially unit-tested |
| State machine (guarded transitions) | `services/message_service.py` | Allowed `status` transitions in one table (`pending→classified→responded`, `*→escalated`); each transition is one atomic status-guarded `UPDATE ... WHERE status IN (allowed_from)`; `rowcount == 0` then an `exists` check yields 404 vs 409 (no read-then-check, race-free) |
| Domain exceptions + central handlers | `core/errors.py` | Services raise `NotFoundError` / `ConflictError`; one handler maps to problem+json |
| Unit of work (session per request) | `get_db` | One transaction per request; service commits once at the end |
| Clock seam | `core/clock.py` | Deterministic timestamps in tests |

## Considered and rejected (YAGNI for a 2h task)

- **Generic base repository / base service** — only two aggregates; duplication is cheaper than the abstraction.
- **Unit-of-work class / event bus** — respond/escalate are two writes in one transaction; plain service method.
- **Alembic migrations** — `Base.metadata.create_all` on startup is enough for SQLite here; note it in the README.
- **Plugin/registry for classifiers** — a keyword table is the whole requirement; an AI classifier is explicitly
  out of scope.
- **Async SQLAlchemy** — no external I/O in scope; sync is simpler to write and test. Decided in `open-questions.md`.
- **Redis/slowapi for rate limiting (bonus)** — if built, use a small in-memory sliding window keyed by
  `property_id` behind a FastAPI dependency.

## Data model notes

- UUID primary keys (`uuid.uuid4` default, stored as `Uuid` type); `created_at` set via the clock seam.
- `GuestMessage.intent` nullable until classified. `status` default `pending`.
- `AutomatedResponse` has FK to message; `GuestMessage.responses` and `.property` relationships are lazy; the
  detail endpoint eager-loads both (`selectinload`/`joinedload`) to avoid N+1.
- Index FK columns and the filter columns (`property_id`, `status`, `intent`, `channel`).
- SQLite does not enforce FKs by default — enable `PRAGMA foreign_keys=ON` on connect; set a busy timeout so concurrent writers wait instead of failing.
- Datetimes: `UtcDateTime` `TypeDecorator` stores UTC and returns timezone-aware values (SQLite drops tzinfo).
