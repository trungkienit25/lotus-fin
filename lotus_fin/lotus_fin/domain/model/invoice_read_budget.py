"""Request-local offline profile; not a production configuration approval."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time


class ReadBudgetExceeded(Exception):
    def __init__(self, axis):
        self.axis = axis
        super().__init__("Invoice read budget exhausted")


@dataclass
class InvoiceReadBudget:
    deadline_at_utc: str
    clock: object = time.monotonic
    utc_clock: object = lambda: datetime.now(timezone.utc)
    counters: dict = field(default_factory=dict)
    limits: dict = field(default_factory=lambda: {
        "list_calls": 2, "document_checks": 51, "metadata_calls": 10,
        "scan_rows": 100, "provider_bytes": 256 * 1024,
        "response_bytes": 64 * 1024, "detail_reads": 1,
    })
    started: float = field(init=False)

    def __post_init__(self):
        self.started = self.clock()
        self.check()

    def check(self):
        deadline = datetime.fromisoformat(self.deadline_at_utc.replace("Z", "+00:00"))
        if deadline.tzinfo is None:
            raise ValueError("Deadline must be timezone-aware")
        if self.clock() - self.started >= 5 or self.utc_clock() >= deadline:
            raise ReadBudgetExceeded("deadline")

    def consume(self, axis, amount=1):
        self.check()
        if axis not in self.limits or type(amount) is not int or amount < 0:
            raise ValueError("Invalid budget observation")
        value = self.counters.get(axis, 0) + amount
        if value > self.limits[axis]:
            raise ReadBudgetExceeded(axis)
        self.counters[axis] = value

    def remaining_seconds(self):
        self.check()
        deadline = datetime.fromisoformat(self.deadline_at_utc.replace("Z", "+00:00"))
        return min(5 - (self.clock() - self.started), (deadline - self.utc_clock()).total_seconds())
