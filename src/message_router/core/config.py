import os
from datetime import timedelta

# At most this many messages may be created per property within the window.
MESSAGE_CREATE_LIMIT = 10
MESSAGE_CREATE_WINDOW = timedelta(minutes=1)

DEFAULT_DATABASE_URL = "sqlite:///message_router.db"


def database_url() -> str:
    """Database URL, overridable through the DATABASE_URL environment variable."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
