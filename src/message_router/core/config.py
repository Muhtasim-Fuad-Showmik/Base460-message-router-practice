import os

DEFAULT_DATABASE_URL = "sqlite:///message_router.db"


def database_url() -> str:
    """Database URL, overridable through the DATABASE_URL environment variable."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
