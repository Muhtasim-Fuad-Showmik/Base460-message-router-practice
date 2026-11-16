# Established patterns — base360-message-router

Conventions for this project. Open `patterns/{slug}.md` only for the layer you are touching.
`api-conventions.md` wins over these on any conflict.

| Section | Summary |
|---|---|
| [Layering](patterns/layering.md) | Router → service → repository → model; what each layer may import and do |
| [Schemas](patterns/schemas.md) | Pydantic Create/Read/Filter schemas, validation in the schema, `from_attributes`, enums shared with models |
| [Models & persistence](patterns/models-and-persistence.md) | SQLAlchemy 2.0 typed models, session per request, explicit commit in the service, bounded + ordered reads, no N+1 |
| [Errors](patterns/errors.md) | Domain exceptions, one handler module, problem+json, codes |
| [Design principles](patterns/design-principles.md) | YAGNI/KISS, rule-of-three, tightest visibility, naming |

Testing lives in `dev-docs/testing.md`; architecture and the chosen/rejected design patterns in
`dev-docs/architecture.md`.
