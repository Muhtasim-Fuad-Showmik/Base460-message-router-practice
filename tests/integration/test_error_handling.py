from fastapi import FastAPI
from fastapi.testclient import TestClient

from message_router.core.errors import ConflictError, ErrorCode, NotFoundError


def _assert_problem(body: dict[str, object], status: int, code: str) -> None:
    assert body["status"] == status
    assert body["code"] == code
    assert body["type"] == "about:blank"
    assert isinstance(body["detail"], str)


def test_unknown_route_returns_problem_json_404(client: TestClient) -> None:
    response = client.get("/nope")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    _assert_problem(response.json(), 404, "NOT_FOUND")


def test_domain_not_found_maps_to_404(app: FastAPI, client: TestClient) -> None:
    @app.get("/_not-found")
    def _raise_not_found() -> None:
        raise NotFoundError(ErrorCode.MESSAGE_NOT_FOUND, "Message missing")

    response = client.get("/_not-found")

    assert response.status_code == 404
    _assert_problem(response.json(), 404, "MESSAGE_NOT_FOUND")
    assert response.json()["detail"] == "Message missing"


def test_domain_conflict_maps_to_409(app: FastAPI, client: TestClient) -> None:
    @app.get("/_conflict")
    def _raise_conflict() -> None:
        raise ConflictError(ErrorCode.MESSAGE_ESCALATED, "Escalated")

    response = client.get("/_conflict")

    assert response.status_code == 409
    _assert_problem(response.json(), 409, "MESSAGE_ESCALATED")


def test_validation_failure_maps_to_422_with_errors(app: FastAPI, client: TestClient) -> None:
    @app.get("/_number")
    def _number(value: int) -> int:
        return value

    response = client.get("/_number", params={"value": "abc"})

    assert response.status_code == 422
    body = response.json()
    _assert_problem(body, 422, "VALIDATION_ERROR")
    assert body["errors"][0]["loc"] == ["query", "value"]
