"""Maze: navigate from one real place at the destination to another."""

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

#: Maze corridor width and turn count per difficulty, passed to the layout stage.
_GRID = {"easy": (6, 6), "medium": (9, 9), "hard": (12, 12)}


@register_activity
class MazeActivity(ActivityGenerator):
    """A path puzzle whose start and finish are places the family will actually see."""

    activity_type = "maze"
    display_name = "Maze"
    educational_goal = (
        "Practises visual planning, sequencing and pencil control, and links two "
        "real locations from the trip."
    )
    min_age = 4
    max_age = 11
    weight = 18
    energy = "active"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        places = self.pick(context, "landmarks", 2)
        if len(places) >= 2:
            start, goal = places[0], places[1]
        elif places:
            start, goal = context.destination, places[0]
        else:
            start, goal = context.destination, self.text(context, "common.this_place")

        collectibles = [*self.pick(context, "local_food", 1), *self.pick(context, "plants", 1)]
        hero = self.hero(context)
        instructions = self.text(context, "maze.instructions", hero=hero, start=start, goal=goal)
        if collectibles:
            instructions += " " + self.text(
                context, "maze.collect", items=self.strings(context).join(collectibles)
            )

        rows, cols = _GRID[planned.difficulty]

        return self.draft(
            title=self.text(context, "maze.title", goal=goal),
            instructions=instructions,
            planned=planned,
            image_brief=ImageBrief(
                subject=f"a maze leading from {start} to {goal}",
                scene=(
                    f"A top-down maze puzzle. A small drawing of {start} marks the entrance "
                    f"in the upper-left corner and a drawing of {goal} marks the exit in the "
                    f"lower-right corner. The maze walls are decorated as {context.destination} "
                    "scenery."
                ),
                elements=tuple(collectibles),
                render_mode=RenderMode.PUZZLE,
                composition=(
                    f"A {rows}x{cols} maze filling the page, corridors wide enough for a "
                    "chunky crayon, exactly one solvable path from entrance to exit."
                ),
                extra_constraints=(
                    "Maze walls must be solid, unbroken and clearly separated from the scenery.",
                    "Exactly one correct route; no dead-end that touches the exit.",
                ),
            ),
            metadata={
                "start": start,
                "goal": goal,
                "grid": {"rows": rows, "cols": cols},
                "collectibles": list(collectibles),
                "hero": hero,
            },
        )
