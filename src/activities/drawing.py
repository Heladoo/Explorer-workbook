"""Drawing Page: an almost empty page with a decorated frame."""

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
class DrawingActivity(ActivityGenerator):
    """Open-ended observational drawing, framed by local motifs."""

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

        motifs = [*self.pick(context, "plants", 2), *self.pick(context, "wildlife", 2)]

        return self.draft(
            title=self.text(context, "drawing.title"),
            instructions=instructions,
            planned=planned,
            image_brief=ImageBrief(
                subject="an empty drawing frame decorated with local motifs",
                scene=(
                    f"A large empty rectangular frame with a decorative border of "
                    f"{context.destination} motifs woven around its edges."
                ),
                elements=tuple(motifs),
                render_mode=RenderMode.FRAME,
                composition=(
                    "The frame occupies about 80% of the page and its interior is completely "
                    "blank white. Only the border carries decoration."
                ),
                extra_constraints=(
                    "The inside of the frame must be pure white — no scenery, no guide lines, "
                    "no faint shapes of any kind.",
                    "Keep the border decoration thin so it never intrudes on the drawing area.",
                ),
            ),
            metadata={"prompt_subject": subject, "border_motifs": motifs, "blank_page": True},
        )
