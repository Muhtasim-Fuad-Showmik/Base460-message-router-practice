import math
from datetime import timedelta
from enum import StrEnum
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    HTTP_ERROR = "HTTP_ERROR"
    PROPERTY_NOT_FOUND = "PROPERTY_NOT_FOUND"
    MESSAGE_NOT_FOUND = "MESSAGE_NOT_FOUND"
    MESSAGE_ALREADY_CLASSIFIED = "MESSAGE_ALREADY_CLASSIFIED"
    MESSAGE_ESCALATED = "MESSAGE_ESCALATED"
    MESSAGE_ALREADY_ESCALATED = "MESSAGE_ALREADY_ESCALATED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class AppError(Exception):
    """Domain error mapped to an RFC 9457 problem response."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, code: ErrorCode, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.headers: dict[str, str] = {}


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT


class RateLimitedError(AppError):
    status_code = HTTPStatus.TOO_MANY_REQUESTS

    def __init__(self, detail: str, retry_after: timedelta) -> None:
        super().__init__(ErrorCode.RATE_LIMIT_EXCEEDED, detail)
        self.headers["Retry-After"] = str(max(1, math.ceil(retry_after.total_seconds())))


def problem_response(
    status_code: int,
    code: ErrorCode,
    detail: str,
    headers: dict[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status_code).phrase,
        "status": status_code,
        "detail": detail,
        "code": code,
        **extra,
    }
    return JSONResponse(body, status_code=status_code, media_type=PROBLEM_JSON, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return problem_response(exc.status_code, exc.code, exc.detail, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return problem_response(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            ErrorCode.VALIDATION_ERROR,
            "Request validation failed",
            errors=errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        is_not_found = exc.status_code == HTTPStatus.NOT_FOUND
        code = ErrorCode.NOT_FOUND if is_not_found else ErrorCode.HTTP_ERROR
        return problem_response(exc.status_code, code, str(exc.detail))
