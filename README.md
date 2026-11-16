# Guest Message Router API

FastAPI + SQLAlchemy + SQLite service that ingests guest messages, classifies them by intent, and manages
automated responses. Spec: `ASSIGNMENT.md`.

> Scaffold only — setup and run instructions are filled in once the app is built.

## Setup (uv)

```
winget install --id=astral-sh.uv -e
uv sync
uv run uvicorn message_router.main:app --reload
```
