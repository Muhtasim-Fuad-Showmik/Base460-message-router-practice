"""Simultaneous transitions on one message: the status-guarded update decides a single winner."""

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from message_router.core.errors import ConflictError
from message_router.models import AutomatedResponse, ResponseType
from message_router.schemas.response import AutomatedResponseCreate
from message_router.services.message_service import MessageService
from tests.conftest import make_message, make_property

WORKERS = 8


def _run_simultaneously(app: FastAPI, action: Callable[[MessageService], Any]) -> list[object]:
    """Run `action` in WORKERS threads, each with its own session, released together."""
    barrier = threading.Barrier(WORKERS)

    def worker() -> object:
        with app.state.session_factory() as session:
            barrier.wait()
            try:
                return action(MessageService(session))
            except ConflictError as error:
                return error

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return [future.result() for future in [pool.submit(worker) for _ in range(WORKERS)]]


def _stored_responses(app: FastAPI, response_type: ResponseType) -> int:
    with app.state.session_factory() as session:
        statement = (
            select(func.count())
            .select_from(AutomatedResponse)
            .where(AutomatedResponse.response_type == response_type)
        )
        return session.scalar(statement) or 0


def test_simultaneous_escalations_produce_exactly_one_winner(
    app: FastAPI, client: TestClient
) -> None:
    stay = make_property(client)
    message = make_message(client, stay["id"])
    message_id = message["id"]

    results = _run_simultaneously(app, lambda service: service.escalate(uuid.UUID(message_id)))

    conflicts = [result for result in results if isinstance(result, ConflictError)]
    winners = [result for result in results if isinstance(result, AutomatedResponse)]
    assert len(winners) == 1
    assert len(conflicts) == WORKERS - 1
    assert _stored_responses(app, ResponseType.ESCALATION_NOTICE) == 1
    assert client.get(f"/messages/{message_id}").json()["status"] == "escalated"


def test_simultaneous_classifications_produce_exactly_one_winner(
    app: FastAPI, client: TestClient
) -> None:
    stay = make_property(client)
    message_id = make_message(client, stay["id"], content="Is there parking?")["id"]

    results = _run_simultaneously(app, lambda service: service.classify(uuid.UUID(message_id)))

    conflicts = [result for result in results if isinstance(result, ConflictError)]
    assert len(conflicts) == WORKERS - 1
    stored = client.get(f"/messages/{message_id}").json()
    assert (stored["status"], stored["intent"]) == ("classified", "amenity_inquiry")


def test_simultaneous_responses_are_all_stored(app: FastAPI, client: TestClient) -> None:
    stay = make_property(client)
    message_id = make_message(client, stay["id"])["id"]
    reply = AutomatedResponseCreate.model_validate({"body": "hi", "response_type": "template"})

    results = _run_simultaneously(
        app, lambda service: service.respond(uuid.UUID(message_id), reply)
    )

    assert all(isinstance(result, AutomatedResponse) for result in results)
    detail = client.get(f"/messages/{message_id}").json()
    assert detail["status"] == "responded"
    assert len(detail["responses"]) == WORKERS
