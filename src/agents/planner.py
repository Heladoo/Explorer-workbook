"""Agent 2 — Workbook Planner.

Decides *which* activities appear, in what order, at what difficulty and for
which child. It never produces content: it hands out slots, and the activity
generators fill them.
"""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

from src.activities.base import ACTIVITY_REGISTRY, ActivityGenerator
from src.models.context import DIFFICULTY_LEVELS, KNOWLEDGE_FIELDS, WorkbookContext
from src.models.plan import PlannedPage

logger = logging.getLogger(__name__)

#: A child's declared interest nudges both activity choice and page focus.
INTEREST_HINTS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # interest: (activity types to favour, knowledge categories to favour)
    "animals": (("wildlife_facts", "matching", "hidden_objects"), ("wildlife",)),
    "wildlife": (("wildlife_facts", "matching", "hidden_objects"), ("wildlife",)),
    "castles": (("coloring", "maze", "spot_difference"), ("landmarks", "history")),
    "history": (("quiz", "spot_difference"), ("history", "landmarks")),
    "trains": (("maze", "coloring"), ("activities", "landmarks")),
    "science": (("quiz", "wildlife_facts"), ("interesting_facts",)),
    "dinosaurs": (("hidden_objects", "matching"), ("wildlife", "history")),
    "food": (("packing", "quiz"), ("local_food",)),
    "art": (("drawing", "coloring"), ("landmarks", "plants")),
    "nature": (("wildlife_facts", "coloring"), ("plants", "wildlife")),
}

#: Focus categories a page can lean on, in the order they are handed out.
FOCUS_ROTATION = (
    "landmarks",
    "wildlife",
    "activities",
    "plants",
    "local_food",
    "history",
    "interesting_facts",
)

MIN_PAGES = 3


class WorkbookPlanner:
    """Builds the ordered slot list for a workbook."""

    def __init__(self, activities: Iterable[ActivityGenerator] | None = None) -> None:
        """``activities`` defaults to every registered plugin (dependency injection
        point for tests and for restricted "teacher mode" style builds)."""
        self._activities = tuple(activities) if activities is not None else None

    def plan(self, context: WorkbookContext) -> tuple[PlannedPage, ...]:
        candidates = [
            activity for activity in self._candidates() if activity.supports(context)
        ]
        if not candidates:
            raise RuntimeError("no activity supports this context — cannot plan a workbook")

        opening = sorted(
            (a for a in candidates if a.pinned == 1), key=lambda a: a.activity_type
        )
        closing = sorted(
            (a for a in candidates if a.pinned == -1), key=lambda a: a.activity_type
        )
        body_pool = [a for a in candidates if a.pinned is None]

        page_count = max(context.page_count, MIN_PAGES)
        body_count = max(page_count - len(opening) - len(closing), 1)
        if not body_pool:
            raise RuntimeError("no unpinned activity available to fill the body of the workbook")

        body = self._select_body(context, body_pool, body_count)
        ordered = [*opening, *body, *closing]

        focus_order = self._focus_order(context)
        pages: list[PlannedPage] = []
        for index, activity in enumerate(ordered):
            is_body = len(opening) <= index < len(opening) + len(body)
            body_index = index - len(opening)
            ratio = body_index / max(body_count - 1, 1) if is_body else 0.0
            difficulty = self._difficulty(context, ratio) if is_body else DIFFICULTY_LEVELS[0]
            pages.append(
                PlannedPage(
                    number=index + 1,
                    activity_type=activity.activity_type,
                    difficulty=difficulty,
                    target_age=self._target_age(context, ratio),
                    focus=focus_order[index % len(focus_order)] if focus_order else None,
                    itinerary_day=self._itinerary_day(context, body_index, body_count)
                    if is_body
                    else None,
                    rationale=self._rationale(activity, difficulty, is_body, index, len(ordered)),
                )
            )
        return tuple(pages)

    # -- internals -------------------------------------------------------

    def _candidates(self) -> tuple[ActivityGenerator, ...]:
        if self._activities is not None:
            return self._activities
        return tuple(cls() for _, cls in sorted(ACTIVITY_REGISTRY.items()))

    def _select_body(
        self,
        context: WorkbookContext,
        pool: Sequence[ActivityGenerator],
        count: int,
    ) -> list[ActivityGenerator]:
        """Fill the body, alternating quiet and active pages and favouring interests."""
        scores = {activity.activity_type: self._score(context, activity) for activity in pool}
        used: dict[str, int] = {}
        chosen: list[ActivityGenerator] = []
        last_energy: str | None = None
        cap_bonus = 0

        while len(chosen) < count:
            available = [
                activity
                for activity in pool
                if used.get(activity.activity_type, 0) < activity.max_per_workbook + cap_bonus
            ]
            if not available:
                # Every activity is at its cap but the book is longer than the
                # catalogue: allow one more repeat of each and keep going.
                cap_bonus += 1
                continue
            pick = min(
                available,
                key=lambda activity: (
                    used.get(activity.activity_type, 0),
                    0 if activity.energy != last_energy else 1,
                    -scores[activity.activity_type],
                    activity.activity_type,
                ),
            )
            chosen.append(pick)
            used[pick.activity_type] = used.get(pick.activity_type, 0) + 1
            last_energy = pick.energy
        return chosen

    def _score(self, context: WorkbookContext, activity: ActivityGenerator) -> int:
        score = activity.weight
        for interest in context.interests:
            favoured, _ = INTEREST_HINTS.get(interest.strip().lower(), ((), ()))
            if activity.activity_type in favoured:
                score += 15
        return score

    def _focus_order(self, context: WorkbookContext) -> tuple[str, ...]:
        """Knowledge categories to rotate through, interests first."""
        preferred: list[str] = []
        for interest in context.interests:
            _, categories = INTEREST_HINTS.get(interest.strip().lower(), ((), ()))
            for category in categories:
                if category not in preferred and context.knowledge.get(category):
                    preferred.append(category)
        rest = [
            category
            for category in FOCUS_ROTATION
            if category not in preferred and context.knowledge.get(category)
        ]
        order = tuple(preferred + rest)
        if order:
            return order
        return tuple(name for name in KNOWLEDGE_FIELDS if context.knowledge.get(name))

    def _difficulty(self, context: WorkbookContext, ratio: float) -> str:
        """Ramp difficulty across the book, capped by the youngest reader's age."""
        if context.difficulty:
            if context.difficulty not in DIFFICULTY_LEVELS:
                raise ValueError(
                    f"unknown difficulty {context.difficulty!r}; "
                    f"choose from {', '.join(DIFFICULTY_LEVELS)}"
                )
            return context.difficulty
        if context.max_age < 5:
            ceiling = 0
        elif context.max_age < 8:
            ceiling = 1
        else:
            ceiling = 2
        step = min(int(ratio * len(DIFFICULTY_LEVELS)), len(DIFFICULTY_LEVELS) - 1)
        return DIFFICULTY_LEVELS[min(step, ceiling)]

    def _target_age(self, context: WorkbookContext, ratio: float) -> int:
        """Early pages address the youngest child, later pages the oldest."""
        spread = context.max_age - context.min_age
        return context.min_age + round(ratio * spread)

    def _itinerary_day(self, context: WorkbookContext, index: int, count: int) -> str | None:
        itinerary = context.trip.itinerary
        if not itinerary or index < 0:
            return None
        position = int(index / max(count, 1) * len(itinerary))
        return itinerary[min(position, len(itinerary) - 1)]

    def _rationale(
        self,
        activity: ActivityGenerator,
        difficulty: str,
        is_body: bool,
        index: int,
        total: int,
    ) -> str:
        if not is_body:
            return "Opens the book." if index == 0 else "Closes the book and looks back."
        return (
            f"{activity.display_name or activity.activity_type} at {difficulty} difficulty, "
            f"page {index + 1} of {total} in the progression."
        )
