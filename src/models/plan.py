"""The planner's output: an ordered list of slots, before any content exists.

Kept in its own module so that activity generators can depend on the plan shape
without importing the planner (which in turn depends on the activity registry).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlannedPage:
    """One slot in the workbook: which activity, how hard, for whom.

    ``focus`` is a hint from the planner about which knowledge category the
    page should lean on (``"wildlife"``, ``"landmarks"``, ...). Activities are
    free to ignore it when it does not apply to them.
    """

    number: int
    activity_type: str
    difficulty: str = "easy"
    target_age: int = 6
    focus: str | None = None
    itinerary_day: str | None = None
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    #: How many page slots this one fills — ``2`` for the double-page centre
    #: spread, ``1`` for everything else. See ``Page.span``.
    span: int = 1

    @property
    def is_first(self) -> bool:
        return self.number == 1

    @property
    def is_spread(self) -> bool:
        return self.span > 1

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "number": self.number,
            "activity_type": self.activity_type,
            "difficulty": self.difficulty,
            "target_age": self.target_age,
            "focus": self.focus,
            "itinerary_day": self.itinerary_day,
            "rationale": self.rationale,
            "metadata": dict(self.metadata),
        }
        if self.span != 1:
            data["span"] = self.span
        return data
