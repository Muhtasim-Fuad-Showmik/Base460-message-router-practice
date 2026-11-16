# Design principles

- **YAGNI / KISS.** Build what `ASSIGNMENT.md` asks. Bonus features only after the core is green.
- **Rule of three.** Duplicate twice; extract on the third use. Two aggregates do not justify a generic base class.
- **Tightest visibility.** Module-private helpers get a leading underscore; export only what other layers import
  (`__all__` where it clarifies).
- **Names describe behaviour**, not the ticket: `MessageService.classify`, `assert_can_respond` — not
  `handle_requirement_4`. Functions are verbs, schemas are nouns, booleans read as questions (`is_`, `can_`).
- **Small functions, early returns, no deep nesting.** Prefer guard clauses for refusals.
- **Comments explain why**, never what. No commented-out code, no TODO without a reason.
- **Constants over magic values**: the default escalation text and keyword table are named module constants.
- **Type everything**; no bare `Any`, no `# type: ignore` without a reason on the same line.
- **Pure core, imperative shell**: rules (classification, transition table) are pure functions; I/O is at the edges.
