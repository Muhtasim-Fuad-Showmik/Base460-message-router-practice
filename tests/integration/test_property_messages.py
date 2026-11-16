import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_message, make_property

REPLY = {"body": "ok", "response_type": "template"}


@pytest.fixture
def stay(client: TestClient) -> dict[str, Any]:
    return make_property(client)


def _get(client: TestClient, property_id: str, **params: int) -> dict[str, Any]:
    response = client.get(f"/properties/{property_id}/messages", params=params)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_property_without_messages_has_a_zeroed_summary(
    client: TestClient, stay: dict[str, Any]
) -> None:
    body = _get(client, stay["id"])

    assert body["summary"] == {
        "total": 0,
        "pending": 0,
        "classified": 0,
        "responded": 0,
        "escalated": 0,
    }
    assert body["messages"] == []


def test_summary_counts_each_status(client: TestClient, stay: dict[str, Any]) -> None:
    pending = make_message(client, stay["id"])
    classified = make_message(client, stay["id"])
    responded = make_message(client, stay["id"])
    escalated_one = make_message(client, stay["id"])
    escalated_two = make_message(client, stay["id"])
    client.patch(f"/messages/{classified['id']}/classify")
    client.post(f"/messages/{responded['id']}/respond", json=REPLY)
    client.post(f"/messages/{escalated_one['id']}/escalate")
    client.post(f"/messages/{escalated_two['id']}/escalate")

    body = _get(client, stay["id"])

    assert body["summary"] == {
        "total": 5,
        "pending": 1,
        "classified": 1,
        "responded": 1,
        "escalated": 2,
    }
    assert {item["id"] for item in body["messages"]} == {
        pending["id"],
        classified["id"],
        responded["id"],
        escalated_one["id"],
        escalated_two["id"],
    }


def test_only_the_requested_propertys_messages_are_included(
    client: TestClient, stay: dict[str, Any]
) -> None:
    other = make_property(client, external_listing_id="other")
    mine = make_message(client, stay["id"])
    make_message(client, other["id"])

    body = _get(client, stay["id"])

    assert body["summary"]["total"] == 1
    assert [item["id"] for item in body["messages"]] == [mine["id"]]


def test_messages_are_newest_first(client: TestClient, stay: dict[str, Any]) -> None:
    for index in range(4):
        make_message(client, stay["id"], content=f"message {index}")

    created_at = [item["created_at"] for item in _get(client, stay["id"])["messages"]]

    assert created_at == sorted(created_at, reverse=True)


def test_pagination_limits_messages_but_not_the_summary(
    client: TestClient, stay: dict[str, Any]
) -> None:
    for index in range(5):
        make_message(client, stay["id"], content=f"message {index}")

    everything = [item["id"] for item in _get(client, stay["id"])["messages"]]
    first = _get(client, stay["id"], skip=0, limit=2)
    last = _get(client, stay["id"], skip=4, limit=2)

    assert len(first["messages"]) == 2
    assert [item["id"] for item in last["messages"]] == everything[4:]
    assert first["summary"]["total"] == last["summary"]["total"] == 5


def test_summary_total_equals_the_sum_of_the_statuses(
    client: TestClient, stay: dict[str, Any]
) -> None:
    for index in range(3):
        make_message(client, stay["id"], content=f"message {index}")
    first = client.get("/messages").json()[0]
    client.patch(f"/messages/{first['id']}/classify")

    summary = _get(client, stay["id"])["summary"]

    assert summary["total"] == sum(v for k, v in summary.items() if k != "total")


def test_unknown_property_returns_404(client: TestClient) -> None:
    response = client.get(f"/properties/{uuid.uuid4()}/messages")

    assert response.status_code == 404
    assert response.json()["code"] == "PROPERTY_NOT_FOUND"


def test_malformed_property_id_returns_422(client: TestClient) -> None:
    assert client.get("/properties/not-a-uuid/messages").status_code == 422


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 101}])
def test_rejects_out_of_range_pagination_with_422(
    client: TestClient, stay: dict[str, Any], params: dict[str, int]
) -> None:
    assert client.get(f"/properties/{stay['id']}/messages", params=params).status_code == 422
