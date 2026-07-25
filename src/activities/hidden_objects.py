"""Find Hidden Objects: a busy destination scene with things tucked inside it."""

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

_OBJECT_COUNT = {"easy": 5, "medium": 7, "hard": 10}


@register_activity
class HiddenObjectsActivity(ActivityGenerator):
    """Search-and-find over local wildlife, plants and food."""

    activity_type = "hidden_objects"
    display_name = "Find the Hidden Objects"
    educational_goal = (
        "Builds sustained visual search and vocabulary for local plants, animals "
        "and objects."
    )
    min_age = 4
    max_age = 11
    weight = 15
    energy = "active"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        count = _OBJECT_COUNT[planned.difficulty]
        pool = [
            *self.pick(context, "wildlife", 4),
            *self.pick(context, "plants", 3),
            *self.pick(context, "local_food", 3),
        ]
        items = list(context.sample(pool, count, key="hidden_objects:items"))

        # Top up with things every trip has, so the count always holds.
        for filler in ("backpack", "water bottle", "sun hat", "camera", "map", "pencil"):
            if len(items) >= count:
                break
            if filler not in items:
                items.append(filler)

        scene_places = self.pick(context, "landmarks", 1)
        scene_place = scene_places[0] if scene_places else context.destination

        return self.draft(
            title=self.text(context, "hidden_objects.title"),
            instructions=self.text(
                context,
                "hidden_objects.instructions",
                count=len(items),
                subject=scene_place,
                items=self.strings(context).join(items),
            ),
            planned=planned,
            image_brief=ImageBrief(
                subject=f"a busy search-and-find scene at {scene_place}",
                scene=(
                    f"A lively wide view of {scene_place} at {context.destination}, full of "
                    "nooks, foliage and small structures where objects can hide."
                ),
                elements=tuple(items),
                render_mode=RenderMode.PUZZLE,
                composition=(
                    "One detailed full-page scene. Each hidden object is drawn completely "
                    "and left partly visible — tucked behind or among scenery, never fully "
                    "covered and never shrunk beyond easy recognition."
                ),
                extra_constraints=(
                    f"Hide exactly these {len(items)} objects, one of each: "
                    + ", ".join(items),
                    "Draw a small empty checkbox row along the bottom margin, one box per "
                    "hidden object, with no text or numbers in them.",
                ),
            ),
            metadata={"scene": scene_place, "objects": items, "object_count": len(items)},
        )
