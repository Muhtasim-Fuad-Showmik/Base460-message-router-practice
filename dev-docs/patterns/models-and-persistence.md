# Models and persistence (SQLAlchemy 2.0, sync)

## Rules

- Typed declarative models: `Mapped[...]` + `mapped_column(...)`; `Uuid` primary keys with a `default=uuid.uuid4`;
  enums stored via `Enum(X, native_enum=False)` (portable on SQLite) with length-checked values.
- `created_at` defaults through the clock seam (`default=utcnow`), never `datetime.now()` inline.
- Sync: `create_engine("sqlite:///...", connect_args={"check_same_thread": False})`, `sessionmaker(expire_on_commit=False)`, `session.execute(select(...))`. Routes are plain `def` (FastAPI runs them in a threadpool).
- Relationships are lazy by default. A read that needs a relation names its loading strategy in the repository
  query (`selectinload` / `joinedload`) — never rely on lazy loads inside a serialisation loop (N+1).
- One session per request (`get_db` yields and closes it). The **service** commits once per mutating use case, so
  `respond` = insert response + update message status in the same transaction; a failure rolls back both.
- Mutations are explicit: `repo.add(entity)` / `session.add` then `commit`; never rely on dirty-checking by
  accident of a flush elsewhere.
- Reads are bounded (`offset/limit` always applied) and deterministically ordered (`created_at DESC, id`).
- Existence checks use `select(exists())`/`session.get`, not loading a list.
- State changes use a status-guarded `UPDATE ... WHERE id = :id AND status IN (...)`; check `rowcount`, never read the status first and write after.
- Enable `PRAGMA foreign_keys=ON` and a busy timeout on SQLite connect; index FK + filter columns.
- Schema creation is `Base.metadata.create_all(engine)` at startup (lifespan); no Alembic for this project.

## Review checks

- DB-01: no `Query` legacy API; `select()` only.
- DB-02: no repository call inside a loop over results.
- DB-03: every list query has limit + order.
- DB-04: only services call `commit`/`rollback`.
- DB-05: no status check followed by a separate write; transitions go through the guarded update.
