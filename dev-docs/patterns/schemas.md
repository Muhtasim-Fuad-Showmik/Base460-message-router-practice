# Schemas (Pydantic v2)

## Rules

- Separate schemas per purpose: `XCreate` (input), `XRead` (output), `XDetail` (output with relations),
  query-filter dependencies for list endpoints. Never reuse an ORM model as a schema.
- All validation the spec states lives in the schema (`EmailStr`, `Field(min_length=1, max_length=2000)`), so the
  422 is produced before the service runs.
- Input schemas: `model_config = ConfigDict(extra="forbid")`. Output schemas: `from_attributes=True`.
- Enums are defined once in `src/message_router/models/enums.py` as `class X(StrEnum)` and imported by models and schemas.
- Optional fields are `T | None = None`; required fields have no default. Do not give request fields defaults that
  hide a missing value (e.g. `status` is never client-supplied on message creation).
- List filters are grouped in a small dependency class/function (`MessageFilter`, `Pagination`) rather than a long
  parameter list repeated per route; `skip`/`limit` constraints are declared once.
- No logic in schemas beyond validators for single-field or cross-field rules.

## Review checks

- SCH-01: every route has `response_model=` and a schema (never `dict`, never an ORM class).
- SCH-02: field constraints from `ASSIGNMENT.md` are enforced in the schema, not re-checked in the service.
- SCH-03: no string literals for enum values outside `enums.py` and tests.
