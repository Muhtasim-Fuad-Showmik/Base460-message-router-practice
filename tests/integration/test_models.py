import uuid
from datetime import UTC

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from message_router.models import Channel, GuestMessage, MessageStatus, Property


def _property() -> Property:
    return Property(name="Sea View", channel=Channel.AIRBNB, external_listing_id="abc-1")


def test_defaults_and_timezone_round_trip(app: FastAPI, client: TestClient) -> None:
    with app.state.session_factory() as session:
        stay = _property()
        session.add(stay)
        session.flush()
        message = GuestMessage(
            property_id=stay.id, guest_name="Ann", guest_email="ann@example.com", content="Hi"
        )
        session.add(message)
        session.commit()
        message_id = message.id

    with app.state.session_factory() as session:
        stored = session.get(GuestMessage, message_id)
        assert stored is not None
        assert stored.status is MessageStatus.PENDING
        assert stored.intent is None
        assert stored.created_at.tzinfo is UTC


def test_message_with_unknown_property_is_rejected_by_foreign_key(
    app: FastAPI, client: TestClient
) -> None:
    with app.state.session_factory() as session:
        session.add(
            GuestMessage(
                property_id=uuid.uuid4(),
                guest_name="Ann",
                guest_email="ann@example.com",
                content="Hi",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
