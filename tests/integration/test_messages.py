import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_message, make_property


@pytest.fixture
def property_id(client: TestClient) -> str:
    return str(make_property(client)["id"])


def _payload(property_id: str, **overrides: Any) -> dict[str, Any]:
    return {
        "property_id": property_id,
        "guest_name": "Ann Guest",
        "guest_email": "ann@example.com",
        "content": "Is there parking?",
        **overrides,
    }


# --- create -----------------------------------------------------------------------------------


def test_create_returns_201_pending_with_no_intent(client: TestClient, property_id: str) -> None:
    response = client.post("/messages", json=_payload(property_id))

    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"])
    assert body["property_id"] == property_id
    assert body["guest_name"] == "Ann Guest"
    assert body["guest_email"] == "ann@example.com"
    assert body["content"] == "Is there parking?"
    assert body["status"] == "pending"
    assert body["intent"] is None
    assert body["created_at"].endswith(("Z", "+00:00"))


def test_create_for_unknown_property_returns_404(client: TestClient) -> None:
    response = client.post("/messages", json=_payload(str(uuid.uuid4())))

    assert response.status_code == 404
    assert response.json()["code"] == "PROPERTY_NOT_FOUND"


def test_create_with_malformed_property_id_returns_422(client: TestClient) -> None:
    assert client.post("/messages", json=_payload("nope")).status_code == 422


def test_create_strips_surrounding_whitespace(client: TestClient, property_id: str) -> None:
    created = make_message(client, property_id, guest_name="  Ann  ", content="  hi  ")

    assert created["guest_name"] == "Ann"
    assert created["content"] == "hi"


@pytest.mark.parametrize("email", ["not-an-email", "ann@", "@example.com", "", " ", "a b@c.com"])
def test_create_rejects_invalid_email_with_422(
    client: TestClient, property_id: str, email: str
) -> None:
    response = client.post("/messages", json=_payload(property_id, guest_email=email))

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("content", ["", "   ", "x" * 2001])
def test_create_rejects_invalid_content_with_422(
    client: TestClient, property_id: str, content: str
) -> None:
    assert client.post("/messages", json=_payload(property_id, content=content)).status_code == 422


@pytest.mark.parametrize("content", ["x", "x" * 2000])
def test_create_accepts_content_at_the_length_bounds(
    client: TestClient, property_id: str, content: str
) -> None:
    assert client.post("/messages", json=_payload(property_id, content=content)).status_code == 201


@pytest.mark.parametrize("guest_name", ["", "   ", "n" * 201])
def test_create_rejects_invalid_guest_name_with_422(
    client: TestClient, property_id: str, guest_name: str
) -> None:
    response = client.post("/messages", json=_payload(property_id, guest_name=guest_name))

    assert response.status_code == 422


@pytest.mark.parametrize("extra", [{"status": "classified"}, {"intent": "other"}, {"id": "x"}])
def test_create_does_not_accept_server_controlled_fields(
    client: TestClient, property_id: str, extra: dict[str, Any]
) -> None:
    assert client.post("/messages", json=_payload(property_id, **extra)).status_code == 422


@pytest.mark.parametrize("missing", ["property_id", "guest_name", "guest_email", "content"])
def test_create_requires_every_field(client: TestClient, property_id: str, missing: str) -> None:
    payload = _payload(property_id)
    del payload[missing]

    assert client.post("/messages", json=payload).status_code == 422


# --- list -------------------------------------------------------------------------------------


def test_list_is_empty_when_nothing_exists(client: TestClient) -> None:
    response = client.get("/messages")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_newest_first(client: TestClient, property_id: str) -> None:
    for index in range(4):
        make_message(client, property_id, content=f"message {index}")

    created_at = [item["created_at"] for item in client.get("/messages").json()]

    assert len(created_at) == 4
    assert created_at == sorted(created_at, reverse=True)


def test_list_filters_by_property(client: TestClient, property_id: str) -> None:
    other_property = str(make_property(client, external_listing_id="other")["id"])
    mine = make_message(client, property_id)
    make_message(client, other_property)

    items = client.get("/messages", params={"property_id": property_id}).json()

    assert [item["id"] for item in items] == [mine["id"]]


def test_list_filters_by_status_and_intent(client: TestClient, property_id: str) -> None:
    pending = make_message(client, property_id, content="hello")
    parking = make_message(client, property_id, content="Is there parking?")
    leak = make_message(client, property_id, content="There is a leak")
    client.patch(f"/messages/{parking['id']}/classify")
    client.patch(f"/messages/{leak['id']}/classify")

    def ids(**params: str) -> set[str]:
        return {item["id"] for item in client.get("/messages", params=params).json()}

    assert ids(status="pending") == {pending["id"]}
    assert ids(status="classified") == {parking["id"], leak["id"]}
    assert ids(intent="amenity_inquiry") == {parking["id"]}
    assert ids(status="classified", intent="maintenance_request") == {leak["id"]}
    assert ids(status="pending", intent="maintenance_request") == set()


@pytest.mark.parametrize("params", [{"status": "bogus"}, {"intent": "bogus"}, {"property_id": "x"}])
def test_list_rejects_invalid_filters_with_422(client: TestClient, params: dict[str, str]) -> None:
    assert client.get("/messages", params=params).status_code == 422


def test_pages_concatenate_to_the_full_list_without_overlap(
    client: TestClient, property_id: str
) -> None:
    for index in range(5):
        make_message(client, property_id, content=f"message {index}")

    everything = [item["id"] for item in client.get("/messages").json()]
    pages = [
        client.get("/messages", params={"skip": skip, "limit": 2}).json() for skip in (0, 2, 4)
    ]

    assert [item["id"] for page in pages for item in page] == everything
    assert [len(page) for page in pages] == [2, 2, 1]


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 101}])
def test_list_rejects_out_of_range_pagination_with_422(
    client: TestClient, params: dict[str, int]
) -> None:
    assert client.get("/messages", params=params).status_code == 422


# --- detail -----------------------------------------------------------------------------------


def test_detail_includes_property_and_responses(client: TestClient) -> None:
    stay = make_property(client, name="Harbour Loft")
    message = make_message(client, stay["id"])

    response = client.get(f"/messages/{message['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == message["id"]
    assert body["property"] == stay
    assert body["responses"] == []


def test_detail_of_unknown_message_returns_404(client: TestClient) -> None:
    response = client.get(f"/messages/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["code"] == "MESSAGE_NOT_FOUND"


def test_detail_with_malformed_id_returns_422(client: TestClient) -> None:
    assert client.get("/messages/not-a-uuid").status_code == 422


# --- classify ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("content", "intent"),
    [
        ("What time is check-in?", "check_in"),
        ("Is the pool open?", "amenity_inquiry"),
        ("The heater is broken", "maintenance_request"),
        ("I need a refund", "booking_question"),
        ("Thanks for everything", "other"),
    ],
)
def test_classify_sets_intent_and_status(
    client: TestClient, property_id: str, content: str, intent: str
) -> None:
    message = make_message(client, property_id, content=content)

    response = client.patch(f"/messages/{message['id']}/classify")

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == intent
    assert body["status"] == "classified"
    assert body["id"] == message["id"]


def test_classify_is_persisted(client: TestClient, property_id: str) -> None:
    message = make_message(client, property_id, content="Is there parking?")
    client.patch(f"/messages/{message['id']}/classify")

    stored = client.get(f"/messages/{message['id']}").json()

    assert stored["intent"] == "amenity_inquiry"
    assert stored["status"] == "classified"


def test_classifying_twice_returns_409_and_keeps_the_first_result(
    client: TestClient, property_id: str
) -> None:
    message = make_message(client, property_id, content="Is there parking?")
    client.patch(f"/messages/{message['id']}/classify")

    response = client.patch(f"/messages/{message['id']}/classify")

    assert response.status_code == 409
    assert response.json()["code"] == "MESSAGE_ALREADY_CLASSIFIED"
    stored = client.get(f"/messages/{message['id']}").json()
    assert (stored["intent"], stored["status"]) == ("amenity_inquiry", "classified")


def test_classify_unknown_message_returns_404(client: TestClient) -> None:
    response = client.patch(f"/messages/{uuid.uuid4()}/classify")

    assert response.status_code == 404
    assert response.json()["code"] == "MESSAGE_NOT_FOUND"


def test_classify_with_malformed_id_returns_422(client: TestClient) -> None:
    assert client.patch("/messages/not-a-uuid/classify").status_code == 422
