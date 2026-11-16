import uuid

from fastapi import APIRouter, status

from message_router.api.deps import MessageServiceDep, PaginationDep, PropertyServiceDep
from message_router.models import Channel, Property
from message_router.schemas.message import MessageRead, PropertyMessages
from message_router.schemas.property import PropertyCreate, PropertyRead

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(data: PropertyCreate, service: PropertyServiceDep) -> Property:
    """Create a property."""
    return service.create(data)


@router.get("", response_model=list[PropertyRead])
def list_properties(
    service: PropertyServiceDep, pagination: PaginationDep, channel: Channel | None = None
) -> list[Property]:
    """List properties, newest first, optionally filtered by channel."""
    return service.list(channel=channel, skip=pagination.skip, limit=pagination.limit)


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(property_id: uuid.UUID, service: PropertyServiceDep) -> Property:
    """Get a single property."""
    return service.get(property_id)


@router.get("/{property_id}/messages", response_model=PropertyMessages)
def list_property_messages(
    property_id: uuid.UUID, service: MessageServiceDep, pagination: PaginationDep
) -> PropertyMessages:
    """A property's messages (newest first, paginated) with a status summary over all of them."""
    summary, messages = service.list_for_property(
        property_id, skip=pagination.skip, limit=pagination.limit
    )
    return PropertyMessages(
        summary=summary, messages=[MessageRead.model_validate(m) for m in messages]
    )
