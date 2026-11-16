# base360-message-router

Practice project: a **Guest Message Router API** (FastAPI + SQLAlchemy (sync) + SQLite) built from a mock Base360.ai
assessment. The full brief is in `ASSIGNMENT.md` — it is the spec; re-read it rather than working from memory.
Time-boxed (~2h). Optimise for a **running, tested, clean** solution over breadth. Bonus items only after the
core is done.

## Commands

Tooling is `uv` (Python 3.12, `src/` layout, `uv_build` backend).

- Install/sync: `uv sync`
- Run: `uv run uvicorn message_router.main:app --reload` (docs at `/docs`)
- Test: `uv run pytest` (single: `uv run pytest tests/unit/test_classifier.py -k keyword`)
- Lint/format: `uv run ruff check . --fix` and `uv run ruff format .`
- Types: `uv run mypy src`
- Add a dependency: `uv add <pkg>` (runtime) or `uv add --dev <pkg>`; never edit `uv.lock` by hand.

Definition of done for any change: `uv run ruff check .`, `uv run mypy src` and `uv run pytest` all pass, and the app still starts.

## Guidelines

- Prefer editing existing files over creating new ones. YAGNI/KISS: no abstraction until a second use exists
  (`dev-docs/patterns/design-principles.md`).
- Plan before building: do not start the main task until the plan is agreed. Decisions (sync, 422-only, whole-word
  matching, transition table) are in `dev-docs/open-questions.md`; follow them and record any new ones there.
- Layering is strict: `api` (routers) → `services` → `repositories` → `models`. Routers contain no business
  logic and no queries; services own rules and transitions; repositories own queries. See
  `dev-docs/architecture.md`.
- Every endpoint declares `response_model=`, an explicit `status_code=`, and uses Pydantic schemas — never return
  ORM objects or dicts directly.
- Persist explicitly: every mutation ends in a repository call that flushes/commits; the service owns the
  transaction boundary (one commit per request).
- Errors are domain exceptions (`src/message_router/core/errors.py`) mapped to RFC 9457 problem responses in one place. Never
  raise `HTTPException` from services or repositories.
- Time goes through `src/message_router/core/clock.py`; never call `datetime.now()` elsewhere.
- Type-hint everything (mypy strict-ish), SQLAlchemy 2.0 style (`Mapped[...]`, `select()`), no legacy `Query`.
- Tests assert behaviour through the public API (HTTP) or a pure function — not private helpers.
- **Never commit without the user's approval.** When a slice is ready, stop and ask the user to review it first; commit only after they approve. Staging is fine, committing is not.
- Use the `commit` skill for commits: conventional commits, small and frequent (the assignment reviews history).

## Docs

Open only what the task calls for:

- `ASSIGNMENT.md` — the spec (source of truth for requirements)
- `dev-docs/architecture.md` — layout, layers, design patterns chosen and rejected
- `dev-docs/patterns.md` — convention index; open `patterns/{slug}.md` for the layer you are touching
- `dev-docs/api-conventions.md` — paths, status codes, error shape, pagination, schema naming
- `dev-docs/testing.md` — test strategy, fixtures, what to cover
- `dev-docs/open-questions.md` — decisions made (sync, 422, whole-word, state table) and what is still open

`dev-docs/api-conventions.md` wins over `dev-docs/patterns/` on any conflict.
