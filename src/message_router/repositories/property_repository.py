import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from message_router.models import Channel, Property


class PropertyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, property_: Property) -> Property:
        self._session.add(property_)
        self._session.flush()
        return property_

    def get(self, property_id: uuid.UUID) -> Property | None:
        return self._session.get(Property, property_id)

    def list(self, *, channel: Channel | None, skip: int, limit: int) -> list[Property]:
        statement = select(Property)
        if channel is not None:
            statement = statement.where(Property.channel == channel)
        statement = statement.order_by(Property.created_at.desc(), Property.id).offset(skip)
        return list(self._session.scalars(statement.limit(limit)))
