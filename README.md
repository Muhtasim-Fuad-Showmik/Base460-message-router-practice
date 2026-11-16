# Guest Message Router API

FastAPI + SQLAlchemy + SQLite service that ingests guest messages, classifies them by intent, and manages
automated responses. The full requirements are in `ASSIGNMENT.md`.

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```
winget install --id=astral-sh.uv -e   # skip if uv is already installed
uv sync
```

Without uv, install the pinned runtime dependencies with pip instead:

```
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run

```
uv run uvicorn message_router.main:app --reload
```

The API is served at `http://localhost:8000`; interactive docs are at `http://localhost:8000/docs`.

The SQLite database is created automatically as `message_router.db` in the working directory. To use a different
database, set `DATABASE_URL` (for example `DATABASE_URL=sqlite:///other.db`).

## Test

```
uv run pytest
```

Optional quality checks:

```
uv run ruff check .
uv run mypy src tests
```
