"""Coloring page: a large, simple scene drawn from the destination's landmarks."""

from __future__ import annotations

from src.activities.base import (
    NOUN_CATEGORIES,
    ActivityGenerator,
    ImageBrief,
    PlannedPage,
    RenderMode,
    register_activity,
)
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft


@register_activity
class ColoringActivity(ActivityGenerator):
    """Free coloring of a real place, with a few things to notice inside it."""

    activity_type = "coloring"
    display_name = "Coloring Page"
    educational_goal = (
        "Develops fine motor control and color choice while introducing a real "
        "place the child will visit."
    )
    min_age = 3
    max_age = 10
    weight = 20
    max_per_workbook = 2
    energy = "calm"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        focus = self.visual_focus(planned, allowed=NOUN_CATEGORIES)
        subjects = self.pick(context, focus, 1) or self.pick(context, "landmarks", 1)
        subject = subjects[0] if subjects else context.destination

        extras = [*self.pick(context, "plants", 2), *self.pick(context, "wildlife", 2)]
        if extras:
            instructions = self.text(
                context,
                "coloring.instructions",
                subject=subject,
                extras=self.strings(context).join(extras[:3]),
            )
        else:
            instructions = self.text(context, "coloring.instructions_plain", subject=subject)

        detail_level = {
            "easy": "very large shapes, few details, thick outlines",
            "medium": "medium-sized shapes with some background detail",
            "hard": "more detailed scene with layered background elements",
        }[planned.difficulty]

        return self.draft(
            title=self.text(context, "coloring.title", subject=subject),
            instructions=instructions,
            planned=planned,
            image_brief=ImageBrief(
                subject=subject,
                scene=(
                    f"{subject} at {context.destination}, seen from a child's eye level, "
                    "with plenty of large open areas to color."
                ),
                elements=tuple(extras),
                render_mode=RenderMode.COLORING,
                composition=f"Single full-page scene, {detail_level}.",
            ),
            metadata={
                "subject": subject,
                "look_for": extras[:3],
                "knowledge_focus": focus,
            },
        )
