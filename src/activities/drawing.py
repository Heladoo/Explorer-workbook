"""Drawing Page: an almost empty page with a blank frame to draw in."""

from __future__ import annotations

from src.activities.base import ActivityGenerator, PlannedPage, register_activity
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft


@register_activity
class DrawingActivity(ActivityGenerator):
    """Open-ended observational drawing on an otherwise blank page."""

    activity_type = "drawing"
    display_name = "Drawing Page"
    educational_goal = (
        "Encourages observation and recall, and gives the child a page that is "
        "entirely their own work."
    )
    min_age = 3
    max_age = 12
    weight = 10
    energy = "calm"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        prompts = self.pick(context, self.visual_focus(planned, default="activities"), 1)
        subject = prompts[0] if prompts else ""
        if subject:
            instructions = self.text(context, "drawing.instructions_prompted", subject=subject)
        else:
            instructions = self.text(context, "drawing.instructions")

        return self.draft(
            title=self.text(context, "drawing.title"),
            instructions=instructions,
            planned=planned,
            metadata={
                "prompt_subject": subject,
                "blank_page": True,
                "needs_illustration": False,
            },
        )
