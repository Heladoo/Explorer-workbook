"""Matching Game: join each subject to its own shadow.

Shadows are used rather than words so the page stays wordless inside the
illustration and works for pre-readers and any language.
"""

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

_PAIR_COUNT = {"easy": 4, "medium": 5, "hard": 6}


@register_activity
class MatchingActivity(ActivityGenerator):
    """Shape recognition over local animals, falling back to local landmarks."""

    activity_type = "matching"
    display_name = "Matching Game"
    educational_goal = (
        "Trains shape recognition and one-to-one correspondence by matching each "
        "subject to its silhouette."
    )
    min_age = 3
    max_age = 9
    weight = 12
    energy = "active"

    def supports(self, context: WorkbookContext) -> bool:
        if not super().supports(context):
            return False
        return bool(context.knowledge.get("wildlife") or context.knowledge.get("landmarks"))

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        count = _PAIR_COUNT[planned.difficulty]
        subjects = self.pick(context, "wildlife", count)
        kind_key = "common.kind_animal"
        if len(subjects) < 3:
            subjects = self.pick(context, "landmarks", count)
            kind_key = "common.kind_place"
        subjects = subjects[:count]

        # The right-hand column is the same set in a different, fixed order.
        shadow_order = list(context.sample(subjects, len(subjects), key="matching:shadows"))

        return self.draft(
            title=self.text(context, "matching.title"),
            instructions=self.text(
                context, "matching.instructions", kind=self.text(context, kind_key)
            ),
            planned=planned,
            image_brief=ImageBrief(
                subject=f"a matching puzzle of {len(subjects)} subjects and their shadows",
                scene=(
                    f"Two vertical columns. The left column shows {len(subjects)} outlined "
                    f"drawings from {context.destination}; the right column shows the same "
                    "shapes as solid black silhouettes in a different order."
                ),
                elements=tuple(subjects),
                render_mode=RenderMode.PUZZLE,
                composition=(
                    "Left column top-to-bottom: " + ", ".join(subjects) + ". "
                    "Right column top-to-bottom (silhouettes): " + ", ".join(shadow_order) + ". "
                    "Wide empty gutter between the columns for the child to draw lines."
                ),
                extra_constraints=(
                    "Each silhouette must be the exact outline of its partner, same pose and "
                    "same size, filled solid black.",
                    "No connecting lines, arrows, numbers or letters anywhere on the page.",
                ),
            ),
            metadata={
                "pair_count": len(subjects),
                "left_column": list(subjects),
                "right_column": shadow_order,
                "answer_key": {subject: shadow_order.index(subject) + 1 for subject in subjects},
                "subject_kind": kind_key.split("_")[-1],
            },
        )
