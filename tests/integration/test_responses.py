import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from message_router.services.message_service import DEFAULT_ESCALATION_BODY
from tests.conftest import make_message, make_property

REPLY = {"body": "Check-in starts at 3pm.", "response_type": "ai_generated"}


@pytest.fixture
def message(client: TestClient) -> dict[str, Any]:
    stay = make_property(client)
    return make_message(client, stay["id"], content="What time is check-in?")


def _detail(client: TestClient, message_id: str) -> dict[str, Any]:
    return client.get(f"/messages/{message_id}").json()  # type: ignore[no-any-return]


# --- respond ----------------------------------------------------------------------------------


def test_respond_creates_a_response_and_marks_the_message_responded(
    client: TestClient, message: dict[str, Any]
) -> None:
    response = client.post(f"/messages/{message['id']}/respond", json=REPLY)

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"])
    assert body["message_id"] == message["id"]
    assert body["body"] == "Check-in starts at 3pm."
    assert body["response_type"] == "ai_generated"
    assert _detail(client, message["id"])["status"] == "responded"


def test_respond_accepts_the_template_type(client: TestClient, message: dict[str, Any]) -> None:
    response = client.post(
        f"/messages/{message['id']}/respond", json={**REPLY, "response_type": "template"}
    )

    assert response.status_code == 201
    assert response.json()["response_type"] == "template"


def test_respond_strips_the_body(client: TestClient, message: dict[str, Any]) -> None:
    response = client.post(f"/messages/{message['id']}/respond", json={**REPLY, "body": "  hi  "})

    assert response.json()["body"] == "hi"


def test_respond_works_after_classification_and_keeps_the_intent(
    client: TestClient, message: dict[str, Any]
) -> None:
    client.patch(f"/messages/{message['id']}/classify")

    response = client.post(f"/messages/{message['id']}/respond", json=REPLY)

    assert response.status_code == 201
    detail = _detail(client, message["id"])
    assert (detail["status"], detail["intent"]) == ("responded", "check_in")


def test_respond_without_classification_leaves_intent_unset(
    client: TestClient, message: dict[str, Any]
) -> None:
    client.post(f"/messages/{message['id']}/respond", json=REPLY)

    detail = _detail(client, message["id"])
    assert (detail["status"], detail["intent"]) == ("responded", None)


def test_repeat_responses_are_all_stored_in_order(
    client: TestClient, message: dict[str, Any]
) -> None:
    first = client.post(f"/messages/{message['id']}/respond", json={**REPLY, "body": "one"})
    second = client.post(f"/messages/{message['id']}/respond", json={**REPLY, "body": "two"})

    assert first.status_code == second.status_code == 201
    detail = _detail(client, message["id"])
    assert detail["status"] == "responded"
    assert [item["body"] for item in detail["responses"]] == ["one", "two"]


def test_respond_to_an_escalated_message_returns_409_and_stores_nothing(
    client: TestClient, message: dict[str, Any]
) -> None:
    client.post(f"/messages/{message['id']}/escalate")

    response = client.post(f"/messages/{message['id']}/respond", json=REPLY)

    assert response.status_code == 409
    assert response.json()["code"] == "MESSAGE_ESCALATED"
    detail = _detail(client, message["id"])
    assert detail["status"] == "escalated"
    assert [item["response_type"] for item in detail["responses"]] == ["escalation_notice"]


def test_respond_to_unknown_message_returns_404(client: TestClient) -> None:
    response = client.post(f"/messages/{uuid.uuid4()}/respond", json=REPLY)

    assert response.status_code == 404
    assert response.json()["code"] == "MESSAGE_NOT_FOUND"


def test_respond_with_malformed_id_returns_422(client: TestClient) -> None:
    assert client.post("/messages/not-a-uuid/respond", json=REPLY).status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {**REPLY, "body": ""},
        {**REPLY, "body": "   "},
        {**REPLY, "body": "x" * 2001},
        {**REPLY, "response_type": "escalation_notice"},
        {**REPLY, "response_type": "bogus"},
        {"body": "no type"},
        {"response_type": "template"},
        {**REPLY, "unexpected": 1},
    ],
)
def test_respond_rejects_invalid_payload_with_422_and_changes_nothing(
    client: TestClient, message: dict[str, Any], payload: dict[str, Any]
) -> None:
    response = client.post(f"/messages/{message['id']}/respond", json=payload)

    assert response.status_code == 422
    detail = _detail(client, message["id"])
    assert (detail["status"], detail["responses"]) == ("pending", [])


def test_respond_documents_only_the_two_client_response_types(app: FastAPI) -> None:
    schema = app.openapi()["components"]["schemas"]["AutomatedResponseCreate"]

    assert schema["properties"]["response_type"]["enum"] == ["ai_generated", "template"]


# --- escalate ---------------------------------------------------------------------------------


def test_escalate_stores_an_escalation_notice_and_marks_the_message_escalated(
    client: TestClient, message: dict[str, Any]
) -> None:
    response = client.post(f"/messages/{message['id']}/escalate")

    assert response.status_code == 201
    body = response.json()
    assert body["message_id"] == message["id"]
    assert body["response_type"] == "escalation_notice"
    assert body["body"] == DEFAULT_ESCALATION_BODY
    assert _detail(client, message["id"])["status"] == "escalated"


def test_escalate_works_from_classified_and_responded(client: TestClient) -> None:
    stay = make_property(client)
    classified = make_message(client, stay["id"])
    responded = make_message(client, stay["id"])
    client.patch(f"/messages/{classified['id']}/classify")
    client.post(f"/messages/{responded['id']}/respond", json=REPLY)

    assert client.post(f"/messages/{classified['id']}/escalate").status_code == 201
    assert client.post(f"/messages/{responded['id']}/escalate").status_code == 201
    assert _detail(client, classified["id"])["status"] == "escalated"
    assert _detail(client, responded["id"])["status"] == "escalated"


def test_escalate_keeps_earlier_responses_and_the_intent(
    client: TestClient, message: dict[str, Any]
) -> None:
    client.patch(f"/messages/{message['id']}/classify")
    client.post(f"/messages/{message['id']}/respond", json=REPLY)

    client.post(f"/messages/{message['id']}/escalate")

    detail = _detail(client, message["id"])
    assert detail["intent"] == "check_in"
    assert [item["response_type"] for item in detail["responses"]] == [
        "ai_generated",
        "escalation_notice",
    ]


def test_escalating_twice_returns_409_and_stores_a_single_notice(
    client: TestClient, message: dict[str, Any]
) -> None:
    client.post(f"/messages/{message['id']}/escalate")

    response = client.post(f"/messages/{message['id']}/escalate")

    assert response.status_code == 409
    assert response.json()["code"] == "MESSAGE_ALREADY_ESCALATED"
    assert len(_detail(client, message["id"])["responses"]) == 1


def test_escalate_unknown_message_returns_404(client: TestClient) -> None:
    response = client.post(f"/messages/{uuid.uuid4()}/escalate")

    assert response.status_code == 404
    assert response.json()["code"] == "MESSAGE_NOT_FOUND"


def test_escalate_with_malformed_id_returns_422(client: TestClient) -> None:
    assert client.post("/messages/not-a-uuid/escalate").status_code == 422


# --- classify after the message moved on ------------------------------------------------------


@pytest.mark.parametrize("move_on", ["respond", "escalate"])
def test_classify_after_respond_or_escalate_returns_409_and_keeps_status(
    client: TestClient, message: dict[str, Any], move_on: str
) -> None:
    if move_on == "respond":
        client.post(f"/messages/{message['id']}/respond", json=REPLY)
    else:
        client.post(f"/messages/{message['id']}/escalate")
    status_before = _detail(client, message["id"])["status"]

    response = client.patch(f"/messages/{message['id']}/classify")

    assert response.status_code == 409
    assert response.json()["code"] == "MESSAGE_ALREADY_CLASSIFIED"
    detail = _detail(client, message["id"])
    assert (detail["status"], detail["intent"]) == (status_before, None)
