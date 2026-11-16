from datetime import UTC, datetime, timedelta


class FakeClock:
    """A controllable replacement for `core.clock.utcnow`."""

    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta: float) -> None:
        self.now += timedelta(**delta)
