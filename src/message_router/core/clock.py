from datetime import UTC, datetime


def utcnow() -> datetime:
    """The single source of "now"; tests patch this to get deterministic timestamps."""
    return datetime.now(UTC)
