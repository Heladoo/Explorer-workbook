"""Wildlife Facts: the animals of the destination, with a place to spot them."""

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

_ANIMAL_COUNT = {"easy": 3, "medium": 4, "hard": 5}


@register_activity
class WildlifeFactsActivity(ActivityGenerator):
    """A fact card page; the only page where light shading is allowed."""

    activity_type = "wildlife_facts"
    display_name = "Wildlife Facts"
    educational_goal = (
        "Builds knowledge of local fauna and habitats, and encourages the child "
        "to look for real animals during the trip."
    )
    min_age = 4
    max_age = 12
    weight = 14
    energy = "calm"
    required_knowledge = ("wildlife",)

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        count = _ANIMAL_COUNT[planned.difficulty]
        animals = self.pick(context, "wildlife", count)
        habitats = self.pick(context, "landmarks", len(animals))

        cards = []
        for index, animal in enumerate(animals):
            if index < len(habitats):
                line = self.text(
                    context, "wildlife_facts.fact_line", animal=animal, place=habitats[index]
                )
            else:
                line = self.text(context, "wildlife_facts.fact_line_plain", animal=animal)
            cards.append({"animal": animal, "caption": line})

        return self.draft(
            title=self.text(context, "wildlife_facts.title", destination=context.display_destination),
            instructions=self.text(
                context,
                "wildlife_facts.instructions",
                count=len(animals),
                destination=context.display_destination,
            ),
            planned=planned,
            image_brief=ImageBrief(
                subject=f"a fact card sheet of {len(animals)} animals from {context.destination}",
                scene=(
                    "A page of equally sized cards, each holding one animal drawn accurately "
                    "and clearly in its natural surroundings."
                ),
                elements=tuple(animals),
                render_mode=RenderMode.ILLUSTRATION,
                composition=(
                    f"{len(animals)} rectangular cards stacked down the page. In each card the "
                    "animal fills the left two-thirds and the right third is left empty for a "
                    "caption and a star the child can color."
                ),
                extra_constraints=(
                    "Draw the animals in this order, one per card: " + ", ".join(animals),
                    "Anatomically believable animals — this page teaches, so no cartoon "
                    "proportions that misrepresent the species.",
                    "Leave the caption strip in each card completely blank.",
                ),
            ),
            metadata={"animals": list(animals), "cards": cards, "star_rating": True},
        )
