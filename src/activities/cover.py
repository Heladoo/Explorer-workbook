"""Cover page: the book's front, personalized with the children's names."""

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


@register_activity
class CoverActivity(ActivityGenerator):
    """The first page: a signature landmark, room for a name, nothing to solve."""

    activity_type = "cover"
    display_name = "Cover"
    educational_goal = (
        "Builds anticipation for the trip and gives the child ownership of the book."
    )
    min_age = 3
    max_age = 12
    pinned = 1
    energy = "calm"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        names = self.strings(context).join(context.child_names)
        if names:
            title = self.text(context, "cover.title_with_names", names=names, destination=context.display_destination)
        else:
            title = self.text(context, "cover.title_plain", destination=context.display_destination)
        # Fixed, not templated on the destination — it already fills the
        # title just above; repeating it here read as redundant.
        instructions = self.text(context, "cover.subtitle")

        landmarks = self.pick(context, "landmarks", 2)
        wildlife = self.pick(context, "wildlife", 1)
        plants = self.pick(context, "plants", 1)

        hero_subject = landmarks[0] if landmarks else context.destination
        elements = [*landmarks, *wildlife, *plants]
        if context.has_children:
            elements.insert(0, f"{len(context.children)} happy children with small backpacks")

        return self.draft(
            title=title,
            instructions=instructions,
            planned=planned,
            image_brief=ImageBrief(
                subject=f"a welcoming cover scene of {hero_subject}",
                scene=(
                    f"A cheerful establishing view of {context.destination}, with "
                    f"{hero_subject} as the centrepiece and children setting off to explore."
                ),
                elements=tuple(elements),
                render_mode=RenderMode.COLORING,
                composition=(
                    "Leave a clear empty banner area across the top third for the title "
                    "and an empty ruled line near the bottom for the child's name."
                ),
                extra_constraints=(
                    "Leave generous white space in the title banner and name line.",
                ),
            ),
            metadata={
                "personalized": bool(names),
                "child_names": list(context.child_names),
                "title_placeholder": True,
                "name_line": True,
            },
        )
