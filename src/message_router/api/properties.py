import uuid

from fastapi import APIRouter, status

from message_router.api.deps import PaginationDep, PropertyServiceDep
from message_router.models import Channel, Property
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
