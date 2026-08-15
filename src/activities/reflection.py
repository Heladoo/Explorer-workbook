"""Reflection Page: the closing page, looking back at the trip."""

from __future__ import annotations

from src.activities.base import (
    ActivityGenerator,
    PlannedPage,
    register_activity,
)
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft

_PROMPT_KEYS = (
    "reflection.prompt_favorite",
    "reflection.prompt_learned",
    "reflection.prompt_next",
    "reflection.prompt_taste",
)


@register_activity
class ReflectionActivity(ActivityGenerator):
    """Closes the book: memory, self-assessment and a star rating."""

    activity_type = "reflection"
    display_name = "Reflection Page"
    educational_goal = (
        "Consolidates memory of the trip and builds early metacognition — "
        "noticing what you enjoyed and what you learned."
    )
    min_age = 4
    max_age = 12
    pinned = -1
    energy = "calm"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        prompt_count = 3 if context.min_age < 7 else 4
        prompts = [self.text(context, key) for key in _PROMPT_KEYS[:prompt_count]]
        stars = context.trip.effective_duration_days or 5
        stars = max(3, min(stars, 10))

        return self.draft(
            title=self.text(context, "reflection.title", destination=context.display_destination),
            instructions=self.text(context, "reflection.instructions"),
            planned=planned,
            metadata={
                "prompts": prompts,
                "writing_lines": prompt_count * 2,
                "stars": stars,
                "closing_page": True,
                "needs_illustration": False,
            },
        )
