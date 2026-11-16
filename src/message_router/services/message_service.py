import uuid
from typing import NoReturn

from sqlalchemy.orm import Session

from message_router.core.errors import ConflictError, ErrorCode, NotFoundError
from message_router.models import (
    AutomatedResponse,
    GuestMessage,
    MessageIntent,
    MessageStatus,
    ResponseType,
)
from message_router.repositories.message_repository import MessageRepository
from message_router.repositories.property_repository import PropertyRepository
from message_router.repositories.response_repository import ResponseRepository
from message_router.schemas.message import MessageCreate
from message_router.schemas.response import AutomatedResponseCreate
from message_router.services import classifier
from message_router.services.transitions import TRANSITIONS, MessageAction

DEFAULT_ESCALATION_BODY = (
    "This conversation has been escalated to a member of our team, "
    "who will follow up with you shortly."
)


class MessageService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._messages = MessageRepository(session)
        self._properties = PropertyRepository(session)
        self._responses = ResponseRepository(session)

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

        # Content never changes, so reading it before the guarded update is race-free.
        self._apply_transition(
            message_id,
            MessageAction.CLASSIFY,
            conflict_code=ErrorCode.MESSAGE_ALREADY_CLASSIFIED,
            conflict_detail="Only pending messages can be classified",
            intent=classifier.classify(message.content),
        )
        self._session.commit()
        self._session.refresh(message)
        return message

    def respond(self, message_id: uuid.UUID, data: AutomatedResponseCreate) -> AutomatedResponse:
        self._apply_transition(
            message_id,
            MessageAction.RESPOND,
            conflict_code=ErrorCode.MESSAGE_ESCALATED,
            conflict_detail="An escalated message cannot receive an automated response",
        )
        response = self._responses.add(
            AutomatedResponse(
                message_id=message_id, body=data.body, response_type=data.response_type
            )
        )
        self._session.commit()
        return response

    def escalate(self, message_id: uuid.UUID) -> AutomatedResponse:
        self._apply_transition(
            message_id,
            MessageAction.ESCALATE,
            conflict_code=ErrorCode.MESSAGE_ALREADY_ESCALATED,
            conflict_detail="Message is already escalated",
        )
        response = self._responses.add(
            AutomatedResponse(
                message_id=message_id,
                body=DEFAULT_ESCALATION_BODY,
                response_type=ResponseType.ESCALATION_NOTICE,
            )
        )
        self._session.commit()
        return response

    def _apply_transition(
        self,
        message_id: uuid.UUID,
        action: MessageAction,
        *,
        conflict_code: ErrorCode,
        conflict_detail: str,
        intent: MessageIntent | None = None,
    ) -> None:
        """Run the action's guarded status update; on a miss, tell 404 from 409."""
        transition = TRANSITIONS[action]
        moved = self._messages.transition(
            message_id,
            allowed_from=transition.allowed_from,
            target=transition.target,
            intent=intent,
        )
        if moved:
            return
        self._session.rollback()  # release the write lock before the follow-up read
        if not self._messages.exists(message_id):
            raise _message_not_found(message_id)
        self._raise_conflict(message_id, conflict_code, conflict_detail)

    def _raise_conflict(self, message_id: uuid.UUID, code: ErrorCode, detail: str) -> NoReturn:
        message = self._messages.get(message_id)
        current = message.status.value if message is not None else "unknown"
        raise ConflictError(code, f"{detail} (status: {current})")


def _message_not_found(message_id: uuid.UUID) -> NotFoundError:
    return NotFoundError(ErrorCode.MESSAGE_NOT_FOUND, f"Message {message_id} not found")
