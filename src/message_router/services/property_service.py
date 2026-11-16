import uuid

from sqlalchemy.orm import Session

from message_router.core.errors import ErrorCode, NotFoundError
from message_router.models import Channel, Property
from message_router.repositories.property_repository import PropertyRepository
from message_router.schemas.property import PropertyCreate


class PropertyService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._properties = PropertyRepository(session)

    def create(self, data: PropertyCreate) -> Property:
        property_ = self._properties.add(Property(**data.model_dump()))
        self._session.commit()
        return property_

    def get(self, property_id: uuid.UUID) -> Property:
        property_ = self._properties.get(property_id)
        if property_ is None:
            raise NotFoundError(ErrorCode.PROPERTY_NOT_FOUND, f"Property {property_id} not found")
        return property_

    def list(self, *, channel: Channel | None, skip: int, limit: int) -> list[Property]:
        return self._properties.list(channel=channel, skip=skip, limit=limit)
