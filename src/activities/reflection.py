"""Reflection Page: the closing page, looking back at the trip."""

from __future__ import annotations

from src.activities.base import (
    ActivityGenerator,
    ImageBrief,
    PlannedPage,
    RenderMode,
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

        motifs = [*self.pick(context, "landmarks", 1), *self.pick(context, "wildlife", 1)]

        return self.draft(
            title=self.text(context, "reflection.title", destination=context.display_destination),
            instructions=self.text(context, "reflection.instructions"),
            planned=planned,
            image_brief=ImageBrief(
                subject="a keepsake page with an empty memory frame and blank writing lines",
                scene=(
                    f"A calm, warm closing page for a trip to {context.destination}: a large "
                    "empty frame for a drawing, blank ruled lines beneath it, and a row of "
                    "outlined stars along the bottom."
                ),
                elements=tuple(motifs),
                render_mode=RenderMode.FRAME,
                composition=(
                    "Top half: one large empty frame. Middle: "
                    f"{prompt_count} groups of two blank ruled lines each. Bottom: a row of "
                    f"{stars} evenly spaced star outlines. Small motifs only in the margins."
                ),
                extra_constraints=(
                    "Frame interior and all ruled lines must be completely empty.",
                    "Stars must be plain outlines, unfilled and unnumbered.",
                ),
            ),
            metadata={
                "prompts": prompts,
                "writing_lines": prompt_count * 2,
                "stars": stars,
                "closing_page": True,
            },
        )
