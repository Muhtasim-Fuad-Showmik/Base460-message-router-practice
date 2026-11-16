import uuid
from http import HTTPStatus

from fastapi import APIRouter

from message_router.api.deps import MessageServiceDep, PaginationDep
from message_router.models import GuestMessage, MessageIntent, MessageStatus
from message_router.schemas.message import MessageCreate, MessageDetail, MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageRead, status_code=HTTPStatus.CREATED)
def create_message(data: MessageCreate, service: MessageServiceDep) -> GuestMessage:
    """Create a guest message. Its status starts as `pending` and its intent is unset."""
    return service.create(data)


@router.get("", response_model=list[MessageRead])
def list_messages(
    service: MessageServiceDep,
    pagination: PaginationDep,
    property_id: uuid.UUID | None = None,
    status: MessageStatus | None = None,
    intent: MessageIntent | None = None,
) -> list[GuestMessage]:
    """List messages, newest first, filtered by property, status and/or intent."""
    return service.list(
        property_id=property_id,
        status=status,
        intent=intent,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{message_id}", response_model=MessageDetail)
def get_message(message_id: uuid.UUID, service: MessageServiceDep) -> GuestMessage:
    """Get a single message with its property and responses."""
    return service.get_detail(message_id)


@router.patch("/{message_id}/classify", response_model=MessageRead)
def classify_message(message_id: uuid.UUID, service: MessageServiceDep) -> GuestMessage:
    """Classify a pending message by keyword. Any non-pending message is a 409."""
    return service.classify(message_id)
