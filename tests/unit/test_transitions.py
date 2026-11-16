import pytest

from message_router.models import MessageStatus
from message_router.services.transitions import TRANSITIONS, MessageAction

P, C, R, E = (
    MessageStatus.PENDING,
    MessageStatus.CLASSIFIED,
    MessageStatus.RESPONDED,
    MessageStatus.ESCALATED,
)


@pytest.mark.parametrize(
    ("action", "from_status", "allowed"),
    [
        (MessageAction.CLASSIFY, P, True),
        (MessageAction.CLASSIFY, C, False),
        (MessageAction.CLASSIFY, R, False),
        (MessageAction.CLASSIFY, E, False),
        (MessageAction.RESPOND, P, True),
        (MessageAction.RESPOND, C, True),
        (MessageAction.RESPOND, R, True),
        (MessageAction.RESPOND, E, False),
        (MessageAction.ESCALATE, P, True),
        (MessageAction.ESCALATE, C, True),
        (MessageAction.ESCALATE, R, True),
        (MessageAction.ESCALATE, E, False),
    ],
)
def test_action_is_allowed_only_from_the_specified_statuses(
    action: MessageAction, from_status: MessageStatus, allowed: bool
) -> None:
    assert (from_status in TRANSITIONS[action].allowed_from) is allowed


@pytest.mark.parametrize(
    ("action", "target"),
    [
        (MessageAction.CLASSIFY, C),
        (MessageAction.RESPOND, R),
        (MessageAction.ESCALATE, E),
    ],
)
def test_action_moves_the_message_to_its_target_status(
    action: MessageAction, target: MessageStatus
) -> None:
    assert TRANSITIONS[action].target is target


def test_every_action_has_a_transition() -> None:
    assert set(TRANSITIONS) == set(MessageAction)
