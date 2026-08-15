"""Word Search (תפזורת): find the destination's words hidden in a letter grid.

The grid is generated here, in full, and travels in the page metadata — so this
page needs no illustration at all. That makes it the cheapest page in the book
to produce.
"""

from __future__ import annotations

from src.activities._wordbank import build_word_bank
from src.activities.base import (
    ActivityGenerator,
    PlannedPage,
    register_activity,
)
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft

_GRID_SIZE = {"easy": 10, "medium": 12, "hard": 14}
#: 8 is the floor at every difficulty — a shorter easy sheet used to feel
#: thin next to the other pages' fixed 16-cell/5-7-item counts.
_WORD_COUNT = {"easy": 8, "medium": 8, "hard": 10}
_MAX_WORD_LENGTH = {"easy": 6, "medium": 8, "hard": 10}

#: (row step, column step) per difficulty — reversed and diagonal come later.
_DIRECTIONS: dict[str, tuple[tuple[int, int], ...]] = {
    "easy": ((0, 1), (1, 0)),
    "medium": ((0, 1), (1, 0), (1, 1)),
    "hard": ((0, 1), (1, 0), (1, 1), (0, -1), (-1, 0), (-1, -1)),
}

_PLACEMENT_ATTEMPTS = 300

#: A diagonal step in either row or column direction is ``(±1, ±1)``. Only
#: "medium"/"hard" ``_DIRECTIONS`` above include one; "easy" never does, so
#: its instructions must not claim a slanted word is ever possible.
_DIAGONAL_STEPS = frozenset({(1, 1), (1, -1), (-1, 1), (-1, -1)})


def _has_diagonal(directions: tuple[tuple[int, int], ...]) -> bool:
    return any(step in _DIAGONAL_STEPS for step in directions)


@register_activity
class WordSearchActivity(ActivityGenerator):
    """A real, solvable letter grid built from the destination's own words."""

    activity_type = "word_search"
    display_name = "Word Search"
    educational_goal = (
        "Builds letter recognition, spelling and systematic visual scanning, "
        "using vocabulary from the place the child is visiting."
    )
    min_age = 6
    max_age = 12
    weight = 14
    energy = "calm"

    def supports(self, context: WorkbookContext) -> bool:
        if not super().supports(context):
            return False
        # Needs enough distinct words to make a grid worth solving.
        return len(build_word_bank(context, count=4, key="supports")) >= 4

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        size = _GRID_SIZE[planned.difficulty]
        entries = build_word_bank(
            context,
            count=_WORD_COUNT[planned.difficulty],
            key=f"word_search:{planned.number}",
            max_length=_MAX_WORD_LENGTH[planned.difficulty],
        )
        words = [entry.word for entry in entries]

        directions = _DIRECTIONS[planned.difficulty]
        grid, placements = self._build_grid(words, size, directions, context, planned)
        placed = [placement["word"] for placement in placements]

        instructions_key = (
            "word_search.instructions_diagonal"
            if _has_diagonal(directions)
            else "word_search.instructions_straight"
        )
        return self.draft(
            title=self.text(context, "word_search.title", destination=context.display_destination),
            instructions=self.text(
                context,
                instructions_key,
                count=len(placed),
                words=self.strings(context).join([word.title() for word in placed]),
            ),
            planned=planned,
            metadata={
                "grid": grid,
                "grid_size": size,
                "words": placed,
                "placements": placements,
                "word_count": len(placed),
                "needs_illustration": False,
            },
        )

    # -- grid construction ------------------------------------------------

    def _build_grid(
        self,
        words: list[str],
        size: int,
        directions: tuple[tuple[int, int], ...],
        context: WorkbookContext,
        planned: PlannedPage,
    ) -> tuple[list[str], list[dict[str, object]]]:
        """Place what fits, then fill the gaps. Longest words go in first."""
        rng = context.rng_for(f"word_search:grid:{planned.number}")
        cells: dict[tuple[int, int], str] = {}
        placements: list[dict[str, object]] = []

        for word in sorted(words, key=len, reverse=True):
            if len(word) > size:
                continue
            placement = self._place(word, cells, size, directions, rng)
            if placement:
                placements.append(placement)

        alphabet = self.strings(context).alphabet
        for row in range(size):
            for column in range(size):
                if (row, column) not in cells:
                    cells[(row, column)] = alphabet[rng.randrange(len(alphabet))]

        grid = ["".join(cells[(row, column)] for column in range(size)) for row in range(size)]
        placements.sort(key=lambda placement: placement["word"])
        return grid, placements

    def _place(
        self,
        word: str,
        cells: dict[tuple[int, int], str],
        size: int,
        directions: tuple[tuple[int, int], ...],
        rng,
    ) -> dict[str, object] | None:
        """Try random positions until the word fits without a letter conflict."""
        for _ in range(_PLACEMENT_ATTEMPTS):
            row_step, column_step = directions[rng.randrange(len(directions))]
            row = rng.randrange(size)
            column = rng.randrange(size)
            end_row = row + row_step * (len(word) - 1)
            end_column = column + column_step * (len(word) - 1)
            if not (0 <= end_row < size and 0 <= end_column < size):
                continue

            coordinates = [
                (row + row_step * index, column + column_step * index)
                for index in range(len(word))
            ]
            if any(
                cells.get(coordinate) not in (None, letter)
                for coordinate, letter in zip(coordinates, word)
            ):
                continue

            for coordinate, letter in zip(coordinates, word):
                cells[coordinate] = letter
            return {
                "word": word,
                "row": row,
                "column": column,
                "direction": [row_step, column_step],
            }
        return None
