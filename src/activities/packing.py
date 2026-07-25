"""Packing Checklist: what to bring, inferred from weather and planned activities."""

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

#: Maps knowledge keywords to a pool of extra items in the locale files.
#: Destination-agnostic: it reacts to what the knowledge says, not to a place.
_KEYWORD_POOLS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("packing.hot_items", ("hot", "sun", "desert", "warm", "dry", "summer", "heat")),
    ("packing.cold_items", ("cold", "snow", "winter", "freez", "chilly", "ice", "alpine")),
    ("packing.rain_items", ("rain", "wet", "monsoon", "shower", "humid", "storm")),
    ("packing.hike_items", ("hike", "hiking", "trek", "trail", "walk", "climb", "mountain")),
    ("packing.water_items", ("swim", "beach", "lake", "river", "sea", "boat", "spring")),
    ("packing.night_items", ("night", "star", "stargaz", "cave", "sunset", "campfire")),
    ("packing.wildlife_items", ("bird", "wildlife", "safari", "animal", "watch")),
)

_ITEM_COUNT = {"easy": 8, "medium": 10, "hard": 12}


@register_activity
class PackingActivity(ActivityGenerator):
    """A tick-box list the child owns, derived from the real conditions."""

    activity_type = "packing"
    display_name = "Packing Checklist"
    educational_goal = (
        "Introduces planning and cause-and-effect: what the weather and the "
        "activities mean for what you carry."
    )
    min_age = 4
    max_age = 12
    weight = 12
    energy = "calm"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        strings = self.strings(context)
        items = list(strings.items("packing.base_items"))

        haystack = " ".join(
            [
                *context.knowledge.get("weather"),
                *context.knowledge.get("activities"),
                *context.interests,
                *context.trip.itinerary,
            ]
        ).lower()

        matched_pools = []
        for pool_key, keywords in _KEYWORD_POOLS:
            if any(keyword in haystack for keyword in keywords):
                matched_pools.append(pool_key)
                for item in strings.items(pool_key):
                    if item not in items:
                        items.append(item)

        limit = _ITEM_COUNT[planned.difficulty]
        items = items[:limit]

        return self.draft(
            title=self.text(context, "packing.title"),
            instructions=self.text(context, "packing.instructions", destination=context.destination),
            planned=planned,
            image_brief=ImageBrief(
                subject="an open explorer backpack surrounded by things to pack",
                scene=(
                    "A friendly open backpack in the centre of the page with the items to "
                    f"pack for {context.destination} arranged around it in a neat grid."
                ),
                elements=tuple(items),
                render_mode=RenderMode.COLORING,
                composition=(
                    f"A grid of {len(items) + 1} equally sized cells. Each cell holds one "
                    "clearly recognisable object drawing with an empty square checkbox beside "
                    "it. The final cell is left completely empty for the child to draw in."
                ),
                extra_constraints=(
                    "Draw exactly these items, one per cell, in this order: " + ", ".join(items),
                    "Checkboxes must be empty outlines — no ticks, no labels, no numbering.",
                ),
            ),
            metadata={
                "items": items,
                "blank_slots": 1,
                "matched_conditions": [key.split(".")[-1] for key in matched_pools],
            },
        )
