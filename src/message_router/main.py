from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import message_router.models  # noqa: F401  (registers tables on Base.metadata)
from message_router.api import messages, properties
from message_router.core.config import (
    MESSAGE_CREATE_LIMIT,
    MESSAGE_CREATE_WINDOW,
    database_url,
)
from message_router.core.database import Base, create_db_engine, create_session_factory
from message_router.core.errors import register_exception_handlers
from message_router.core.rate_limit import SlidingWindowRateLimiter


def create_app(
    url: str | None = None, *, message_rate_limiter: SlidingWindowRateLimiter | None = None
) -> FastAPI:
    engine = create_db_engine(url or database_url())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        Base.metadata.create_all(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Guest Message Router API", version="0.1.0", lifespan=lifespan)
    app.state.session_factory = create_session_factory(engine)
    app.state.message_rate_limiter = message_rate_limiter or SlidingWindowRateLimiter(
        limit=MESSAGE_CREATE_LIMIT, window=MESSAGE_CREATE_WINDOW
    )
    register_exception_handlers(app)
    app.include_router(properties.router)
    app.include_router(messages.router)
    return app


app = create_app()
