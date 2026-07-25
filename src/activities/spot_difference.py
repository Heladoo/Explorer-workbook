"""Spot the Difference: two near-identical scenes from the destination."""

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

#: How many differences to hide, per difficulty.
_DIFFERENCE_COUNT = {"easy": 4, "medium": 6, "hard": 8}

#: The kinds of change the layout stage may apply, in priority order.
_CHANGE_KINDS = ("missing", "extra", "moved", "resized")


@register_activity
class SpotDifferenceActivity(ActivityGenerator):
    """Trains close observation on a scene the child will recognise on the trip."""

    activity_type = "spot_difference"
    display_name = "Spot the Difference"
    educational_goal = (
        "Sharpens visual discrimination and attention to detail through careful "
        "comparison of two scenes."
    )
    min_age = 4
    max_age = 12
    weight = 16
    energy = "active"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        focus = self.visual_focus(planned, allowed=NOUN_CATEGORIES)
        subjects = self.pick(context, focus, 1) or self.pick(context, "landmarks", 1)
        subject = subjects[0] if subjects else context.destination

        count = _DIFFERENCE_COUNT[planned.difficulty]
        pool = [
            *self.pick(context, "wildlife", 3),
            *self.pick(context, "plants", 3),
            *self.pick(context, "local_food", 2),
            *self.pick(context, "activities", 2),
        ]
        items = context.sample(pool, count, key="spot_difference:items") if pool else ()

        differences = []
        for index, item in enumerate(items):
            kind = _CHANGE_KINDS[index % len(_CHANGE_KINDS)]
            differences.append(
                {
                    "item": item,
                    "kind": kind,
                    "description": self.text(
                        context, f"spot_difference.change_{kind}", item=item
                    ),
                }
            )

        return self.draft(
            title=self.text(context, "spot_difference.title"),
            instructions=self.text(
                context, "spot_difference.instructions", subject=subject, count=count
            ),
            planned=planned,
            image_brief=ImageBrief(
                subject=f"two nearly identical scenes of {subject}",
                scene=(
                    f"The same view of {subject} at {context.destination} drawn twice: the "
                    "top half is the original, the bottom half repeats it with small changes."
                ),
                elements=tuple(item for item in items),
                render_mode=RenderMode.PUZZLE,
                composition=(
                    "Portrait page split into two equal panels stacked vertically, each with "
                    f"a thin frame, containing exactly {count} deliberate differences."
                ),
                extra_constraints=(
                    f"Introduce exactly {count} differences between the two panels: "
                    + "; ".join(f"{d['kind']} — {d['item']}" for d in differences),
                    "Everything not listed as a difference must be pixel-for-pixel identical.",
                ),
            ),
            metadata={
                "subject": subject,
                "difference_count": count,
                "differences": differences,
            },
        )
