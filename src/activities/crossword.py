"""Crossword: an interlocking grid built from the destination's own vocabulary.

Like the word search, the whole puzzle is generated here and carried in the
page metadata, so the page needs no illustration. Clues come free: a knowledge
phrase with its answer blanked out ("The big Bedouin hospitality ___") is a
natural clue, and single-word entries fall back to a category clue.
"""

from __future__ import annotations

from typing import Any

from src.activities._wordbank import WordEntry, build_word_bank
from src.activities.base import (
    ActivityGenerator,
    ImageBrief,
    PlannedPage,
    RenderMode,
    register_activity,
)
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft

_WORD_COUNT = {"easy": 5, "medium": 7, "hard": 9}
_MAX_WORD_LENGTH = {"easy": 7, "medium": 8, "hard": 9}

ACROSS = (0, 1)
DOWN = (1, 0)


@register_activity
class CrosswordActivity(ActivityGenerator):
    """A small interlocking crossword, solvable and with a real answer key."""

    activity_type = "crossword"
    display_name = "Crossword"
    educational_goal = (
        "Practises spelling, reading comprehension and inference — the child has "
        "to work out the answer from a clue and fit it to the letters already there."
    )
    min_age = 7
    max_age = 12
    weight = 12
    energy = "calm"

    def supports(self, context: WorkbookContext) -> bool:
        if not super().supports(context):
            return False
        return len(build_word_bank(context, count=4, key="crossword:supports")) >= 4

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        entries = build_word_bank(
            context,
            count=_WORD_COUNT[planned.difficulty] + 3,  # spares for words that won't fit
            key=f"crossword:{planned.number}",
            max_length=_MAX_WORD_LENGTH[planned.difficulty],
        )
        puzzle = self._build(entries, _WORD_COUNT[planned.difficulty], context)

        clue_count = len(puzzle["across"]) + len(puzzle["down"])
        return self.draft(
            title=self.text(context, "crossword.title", destination=context.display_destination),
            instructions=self.text(context, "crossword.instructions", count=clue_count),
            planned=planned,
            image_brief=ImageBrief(
                subject="a decorative border for a crossword page",
                scene=(
                    f"A thin decorative border of {context.destination} motifs framing an "
                    "otherwise completely empty page."
                ),
                elements=tuple(self.pick(context, "landmarks", 2)),
                render_mode=RenderMode.FRAME,
                composition=(
                    "Border only, no more than 15 mm wide. The centre of the page stays "
                    "blank white — the crossword grid and clues are typeset there."
                ),
                extra_constraints=(
                    "Do not draw a grid, squares, numbers, letters or clues.",
                    "This border is optional decoration; the page is complete without it.",
                ),
            ),
            metadata={
                **puzzle,
                "clue_count": clue_count,
                "illustration": "decorative",
                "needs_illustration": False,
            },
        )

    # -- puzzle construction ----------------------------------------------

    def _build(
        self, entries: tuple[WordEntry, ...], wanted: int, context: WorkbookContext
    ) -> dict[str, Any]:
        """Place words one at a time, each crossing one already on the grid."""
        ordered = sorted(entries, key=lambda entry: len(entry.word), reverse=True)
        cells: dict[tuple[int, int], str] = {}
        placed: list[dict[str, Any]] = []

        for entry in ordered:
            if len(placed) >= wanted:
                break
            if any(existing["entry"].word == entry.word for existing in placed):
                continue
            if not placed:
                self._write(cells, entry.word, 0, 0, ACROSS)
                placed.append(
                    {"entry": entry, "row": 0, "column": 0, "direction": ACROSS}
                )
                continue
            spot = self._find_spot(entry.word, cells, placed)
            if spot:
                row, column, direction = spot
                self._write(cells, entry.word, row, column, direction)
                placed.append(
                    {"entry": entry, "row": row, "column": column, "direction": direction}
                )

        return self._finalize(cells, placed, context)

    def _write(
        self,
        cells: dict[tuple[int, int], str],
        word: str,
        row: int,
        column: int,
        direction: tuple[int, int],
    ) -> None:
        for index, letter in enumerate(word):
            cells[(row + direction[0] * index, column + direction[1] * index)] = letter

    def _find_spot(
        self,
        word: str,
        cells: dict[tuple[int, int], str],
        placed: list[dict[str, Any]],
    ) -> tuple[int, int, tuple[int, int]] | None:
        """Find the placement that crosses an existing word and keeps the grid tightest.

        Taking the first legal spot makes the puzzle sprawl across the page;
        scoring every candidate by the bounding box it would produce keeps the
        grid compact enough to print at a readable square size.
        """
        candidates: list[tuple[tuple[int, int, int], int, int, tuple[int, int]]] = []
        for existing in placed:
            direction = DOWN if existing["direction"] == ACROSS else ACROSS
            existing_word = existing["entry"].word
            for existing_index, existing_letter in enumerate(existing_word):
                cross = (
                    existing["row"] + existing["direction"][0] * existing_index,
                    existing["column"] + existing["direction"][1] * existing_index,
                )
                for index, letter in enumerate(word):
                    if letter != existing_letter:
                        continue
                    row = cross[0] - direction[0] * index
                    column = cross[1] - direction[1] * index
                    if self._fits(word, cells, row, column, direction):
                        candidates.append(
                            (self._compactness(word, cells, row, column, direction),
                             row, column, direction)
                        )
        if not candidates:
            return None
        score, row, column, direction = min(candidates)
        return row, column, direction

    def _compactness(
        self,
        word: str,
        cells: dict[tuple[int, int], str],
        row: int,
        column: int,
        direction: tuple[int, int],
    ) -> tuple[int, int, int]:
        """Rank a candidate: smaller area first, then squarer, then leftmost."""
        rows = [position[0] for position in cells] + [
            row, row + direction[0] * (len(word) - 1)
        ]
        columns = [position[1] for position in cells] + [
            column, column + direction[1] * (len(word) - 1)
        ]
        height = max(rows) - min(rows) + 1
        width = max(columns) - min(columns) + 1
        return (height * width, abs(height - width), column)

    def _fits(
        self,
        word: str,
        cells: dict[tuple[int, int], str],
        row: int,
        column: int,
        direction: tuple[int, int],
    ) -> bool:
        """A placement is legal only if it never creates an unintended word."""
        row_step, column_step = direction
        # The squares immediately before and after the word must be empty.
        if (row - row_step, column - column_step) in cells:
            return False
        if (row + row_step * len(word), column + column_step * len(word)) in cells:
            return False

        crossings = 0
        for index, letter in enumerate(word):
            position = (row + row_step * index, column + column_step * index)
            existing = cells.get(position)
            if existing is not None:
                if existing != letter:
                    return False
                crossings += 1
                continue
            # A fresh square must not sit alongside another word.
            for sign in (-1, 1):
                neighbour = (
                    position[0] + column_step * sign,
                    position[1] + row_step * sign,
                )
                if neighbour in cells:
                    return False
        return crossings == 1

    def _finalize(
        self,
        cells: dict[tuple[int, int], str],
        placed: list[dict[str, Any]],
        context: WorkbookContext,
    ) -> dict[str, Any]:
        """Normalize coordinates, number the squares, and build the clue lists."""
        if not cells:
            return {"rows": 0, "columns": 0, "layout": [], "solution": [], "across": [], "down": []}

        min_row = min(row for row, _ in cells)
        min_column = min(column for _, column in cells)
        normalized = {
            (row - min_row, column - min_column): letter for (row, column), letter in cells.items()
        }
        rows = max(row for row, _ in normalized) + 1
        columns = max(column for _, column in normalized) + 1

        numbers: dict[tuple[int, int], int] = {}
        next_number = 1
        for row in range(rows):
            for column in range(columns):
                if (row, column) not in normalized:
                    continue
                starts_across = (row, column - 1) not in normalized and (
                    row,
                    column + 1,
                ) in normalized
                starts_down = (row - 1, column) not in normalized and (
                    row + 1,
                    column,
                ) in normalized
                if starts_across or starts_down:
                    numbers[(row, column)] = next_number
                    next_number += 1

        across: list[dict[str, Any]] = []
        down: list[dict[str, Any]] = []
        for entry in placed:
            row = entry["row"] - min_row
            column = entry["column"] - min_column
            clue = {
                "number": numbers.get((row, column), 0),
                "clue": self._clue(entry["entry"], context),
                "answer": entry["entry"].word,
                "row": row,
                "column": column,
                "length": len(entry["entry"].word),
                "category": entry["entry"].category,
            }
            (across if entry["direction"] == ACROSS else down).append(clue)
        across.sort(key=lambda clue: clue["number"])
        down.sort(key=lambda clue: clue["number"])

        # ``layout`` is what gets printed: "." is a writable square, "#" is blank
        # page. ``solution`` is the answer key, never rendered on the child's page.
        layout = [
            "".join("." if (row, column) in normalized else "#" for column in range(columns))
            for row in range(rows)
        ]
        solution = [
            "".join(normalized.get((row, column), "#") for column in range(columns))
            for row in range(rows)
        ]

        return {
            "rows": rows,
            "columns": columns,
            "layout": layout,
            "solution": solution,
            "numbers": [
                {"row": row, "column": column, "number": number}
                for (row, column), number in sorted(numbers.items())
            ],
            "across": across,
            "down": down,
        }

    def _clue(self, entry: WordEntry, context: WorkbookContext) -> str:
        """Blank the answer out of its own phrase, or fall back to a category clue."""
        blanked = entry.blanked_source()
        if blanked and blanked != "___":
            return blanked
        return self.text(
            context, f"crossword.clue_{entry.category}", destination=context.display_destination
        )
