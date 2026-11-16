# Errors

- Domain exceptions live in `src/message_router/core/errors.py`: base `AppError(code, status_code, detail)` with
  `NotFoundError` (404) and `ConflictError` (409). Add a subclass only when a handler needs different behaviour.
- Error codes are an `ErrorCode(StrEnum)`, e.g. `PROPERTY_NOT_FOUND`, `MESSAGE_NOT_FOUND`,
  `MESSAGE_ALREADY_CLASSIFIED`, `MESSAGE_ESCALATED`. The code is the stable contract; `detail` is human text.
- Services raise; they never build HTTP responses. `register_exception_handlers(app)` in `core/errors.py` maps
  `AppError` and `RequestValidationError` to `application/problem+json` (shape in `api-conventions.md`).
- Check cheap refusals first (existence, then state) before doing any writes.
- Catch `IntegrityError` only where a race is realistic; there is no such case in the base scope.
- Unexpected exceptions are left to the framework's 500 — do not blanket `except Exception`.

## Review checks

- ERR-01: no `HTTPException` outside `core/errors.py`.
- ERR-02: every domain exception has a code in `ErrorCode`, covered by an integration test asserting status + code.
