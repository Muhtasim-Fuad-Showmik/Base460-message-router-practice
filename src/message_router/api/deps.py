from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from message_router.services.message_service import MessageService
from message_router.services.property_service import PropertyService

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


def get_db(request: Request) -> Iterator[Session]:
    """One session per request, closed afterwards. Services own commit/rollback."""
    with request.app.state.session_factory() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


@dataclass(frozen=True)
class Pagination:
    skip: int
    limit: int


def get_pagination(
    skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description="Maximum number of items to return")
    ] = DEFAULT_PAGE_SIZE,
) -> Pagination:
    return Pagination(skip=skip, limit=limit)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]


def get_property_service(session: DbSession) -> PropertyService:
    return PropertyService(session)


PropertyServiceDep = Annotated[PropertyService, Depends(get_property_service)]


def get_message_service(session: DbSession) -> MessageService:
    return MessageService(session)


MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
