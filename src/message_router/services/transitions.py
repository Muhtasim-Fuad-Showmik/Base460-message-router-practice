"""The message status state machine: the single table every transition is checked against."""

from dataclasses import dataclass
from enum import StrEnum

from message_router.models.enums import MessageStatus


class MessageAction(StrEnum):
    CLASSIFY = "classify"
    RESPOND = "respond"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class Transition:
    allowed_from: frozenset[MessageStatus]
    target: MessageStatus


_ANY_BUT_ESCALATED = frozenset(
    {MessageStatus.PENDING, MessageStatus.CLASSIFIED, MessageStatus.RESPONDED}
)

TRANSITIONS: dict[MessageAction, Transition] = {
    MessageAction.CLASSIFY: Transition(
        frozenset({MessageStatus.PENDING}), MessageStatus.CLASSIFIED
    ),
    MessageAction.RESPOND: Transition(_ANY_BUT_ESCALATED, MessageStatus.RESPONDED),
    MessageAction.ESCALATE: Transition(_ANY_BUT_ESCALATED, MessageStatus.ESCALATED),
}
