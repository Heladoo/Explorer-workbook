"""Route Map: one illustrated map of the real itinerary, stop by stop.

Only makes sense once there is an actual *route* to draw — an itinerary of
one or two stops is just an origin and a destination, not a path connecting
several. Modeled on ``coloring.py``/``cover.py``: a single :class:`ImageBrief`,
not a :class:`SymbolBrief` grid, because a hand-drawn route map is one
picture, not a table of small ones.

This page exists because of what a human did, not what a generator guessed:
comparing a machine-generated Pelion workbook to the same book after a human
hand-edited it into a polished final version, the human replaced a generic
"color the goats" coloring page with a full illustrated route map showing the
real itinerary stops in order, connected by a path, bookended by the two
country names. That edit is the strongest possible signal of what this page
should be.
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

#: Below this many stops, "connect them in order" isn't a route worth
#: drawing — one or two stops is just an origin and a destination, not a
#: path with anything to show in between.
_MIN_STOPS = 3


@register_activity
class MapActivity(ActivityGenerator):
    """An illustrated map of the real trip, stop to stop."""

    activity_type = "map"
    display_name = "Route Map"
    educational_goal = (
        "Builds a sense of the whole journey — where each stop sits along the "
        "way, not just what happens at any single one of them."
    )
    min_age = 3
    max_age = 12
    weight = 10
    energy = "calm"

    def supports(self, context: WorkbookContext) -> bool:
        if not super().supports(context):
            return False
        # A route needs at least a beginning, a middle and an end to read as
        # a route at all, rather than as a single hop from A to B.
        return len(context.trip.itinerary) >= _MIN_STOPS

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        # supports() guarantees >= _MIN_STOPS during real planning, but
        # generate() itself is also exercised directly (e.g. the shared
        # activity contract test) against contexts that never checked
        # supports() first, so this stays honest for a short or empty
        # itinerary too, falling back to the destination alone.
        itinerary = context.trip.itinerary or (context.destination,)
        stops = self.strings(context).join(itinerary)

        return self.draft(
            title=self.text(context, "map.title", destination=context.display_destination),
            instructions=self.text(context, "map.instructions", stops=stops),
            planned=planned,
            image_brief=ImageBrief(
                subject=f"an illustrated route map of the trip to {context.destination}",
                scene=(
                    "An illustrated route map showing each stop of the trip in sequence, "
                    f"connected by a path or road, from {itinerary[0]} to {itinerary[-1]}."
                ),
                elements=tuple(itinerary),
                render_mode=RenderMode.ILLUSTRATION,
                composition=(
                    "A single full-page map view, every stop labelled in order along one "
                    "continuous path, simple and easy for a child to trace with a finger."
                ),
            ),
            metadata={
                "itinerary": list(itinerary),
                "stop_count": len(itinerary),
            },
        )
