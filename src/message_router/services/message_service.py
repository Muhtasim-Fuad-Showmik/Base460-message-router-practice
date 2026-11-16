import uuid

from sqlalchemy.orm import Session

from message_router.core.errors import ConflictError, ErrorCode, NotFoundError
from message_router.models import GuestMessage, MessageIntent, MessageStatus
from message_router.repositories.message_repository import MessageRepository
from message_router.repositories.property_repository import PropertyRepository
from message_router.schemas.message import MessageCreate
from message_router.services import classifier
from message_router.services.transitions import TRANSITIONS, MessageAction


class MessageService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._messages = MessageRepository(session)
        self._properties = PropertyRepository(session)

    def create(self, data: MessageCreate) -> GuestMessage:
        if not self._properties.exists(data.property_id):
            raise NotFoundError(
                ErrorCode.PROPERTY_NOT_FOUND, f"Property {data.property_id} not found"
            )
        message = self._messages.add(GuestMessage(**data.model_dump()))
        self._session.commit()
        return message

    def get_detail(self, message_id: uuid.UUID) -> GuestMessage:
        message = self._messages.get_with_property_and_responses(message_id)
        if message is None:
            raise _message_not_found(message_id)
        return message

    def list(
        self,
        *,
        property_id: uuid.UUID | None,
        status: MessageStatus | None,
        intent: MessageIntent | None,
        skip: int,
        limit: int,
    ) -> list[GuestMessage]:
        return self._messages.list(
            property_id=property_id, status=status, intent=intent, skip=skip, limit=limit
        )

    def classify(self, message_id: uuid.UUID) -> GuestMessage:
        message = self._messages.get(message_id)
        if message is None:
            raise _message_not_found(message_id)

        transition = TRANSITIONS[MessageAction.CLASSIFY]
        moved = self._messages.transition(
            message_id,
            allowed_from=transition.allowed_from,
            target=transition.target,
            intent=classifier.classify(message.content),
        )
        if not moved:
            self._session.refresh(message)
            raise ConflictError(
                ErrorCode.MESSAGE_ALREADY_CLASSIFIED,
                f"Only pending messages can be classified; this one is {message.status.value}",
            )
        self._session.commit()
        self._session.refresh(message)
        return message


def _message_not_found(message_id: uuid.UUID) -> NotFoundError:
    return NotFoundError(ErrorCode.MESSAGE_NOT_FOUND, f"Message {message_id} not found")
