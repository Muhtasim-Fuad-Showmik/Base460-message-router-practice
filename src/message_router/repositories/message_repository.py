import uuid
from collections.abc import Collection
from typing import Any, cast

from sqlalchemy import CursorResult, exists, func, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from message_router.models import GuestMessage, MessageIntent, MessageStatus


class MessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, message: GuestMessage) -> GuestMessage:
        self._session.add(message)
        self._session.flush()
        return message

    def get(self, message_id: uuid.UUID) -> GuestMessage | None:
        return self._session.get(GuestMessage, message_id)

    def exists(self, message_id: uuid.UUID) -> bool:
        statement = select(exists().where(GuestMessage.id == message_id))
        return bool(self._session.scalar(statement))

    def get_with_property_and_responses(self, message_id: uuid.UUID) -> GuestMessage | None:
        statement = (
            select(GuestMessage)
            .where(GuestMessage.id == message_id)
            .options(joinedload(GuestMessage.property), selectinload(GuestMessage.responses))
        )
        return self._session.scalars(statement).one_or_none()

    def list(
        self,
        *,
        property_id: uuid.UUID | None,
        status: MessageStatus | None,
        intent: MessageIntent | None,
        skip: int,
        limit: int,
    ) -> list[GuestMessage]:
        statement = select(GuestMessage)
        if property_id is not None:
            statement = statement.where(GuestMessage.property_id == property_id)
        if status is not None:
            statement = statement.where(GuestMessage.status == status)
        if intent is not None:
            statement = statement.where(GuestMessage.intent == intent)
        statement = statement.order_by(GuestMessage.created_at.desc(), GuestMessage.id)
        return list(self._session.scalars(statement.offset(skip).limit(limit)))

    def count_by_status(self, property_id: uuid.UUID) -> dict[MessageStatus, int]:
        """Message counts per status for one property, in a single grouped query."""
        statement = (
            select(GuestMessage.status, func.count())
            .where(GuestMessage.property_id == property_id)
            .group_by(GuestMessage.status)
        )
        return dict(self._session.execute(statement).tuples().all())

    def transition(
        self,
        message_id: uuid.UUID,
        *,
        allowed_from: Collection[MessageStatus],
        target: MessageStatus,
        intent: MessageIntent | None = None,
    ) -> bool:
        """Atomically move the message to `target` if its status is still in `allowed_from`.

        One conditional UPDATE, so a concurrent change cannot slip between a check and a write.
        Returns False when no row matched (the message is missing or in another status).
        """
        values: dict[str, Any] = {"status": target}
        if intent is not None:
            values["intent"] = intent
        statement = (
            update(GuestMessage)
            .where(GuestMessage.id == message_id, GuestMessage.status.in_(allowed_from))
            .values(**values)
        )
        result = cast(
            "CursorResult[Any]",
            self._session.execute(statement, execution_options={"synchronize_session": False}),
        )
        return result.rowcount == 1
