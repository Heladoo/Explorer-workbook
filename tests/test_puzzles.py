"""Word search and crossword must be genuinely solvable.

These pages carry no illustration — the puzzle *is* the data — so the tests
solve them rather than checking that fields are populated.
"""

from __future__ import annotations

import pytest

from src.activities._wordbank import build_word_bank, puzzle_word
from src.activities.base import get_generator
from src.models.context import DIFFICULTY_LEVELS, DestinationKnowledge, WorkbookContext
from src.models.plan import PlannedPage

_DIRECTIONS = (
    (0, 1), (1, 0), (1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1), (-1, 1),
)


def _slot(activity_type: str, difficulty: str = "medium", number: int = 7) -> PlannedPage:
    return PlannedPage(number=number, activity_type=activity_type, difficulty=difficulty)


def _find(grid: list[str], word: str) -> bool:
    """Search the grid in all eight directions."""
    size = len(grid)
    for row in range(size):
        for column in range(len(grid[row])):
            for row_step, column_step in _DIRECTIONS:
                end_row = row + row_step * (len(word) - 1)
                end_column = column + column_step * (len(word) - 1)
                if not (0 <= end_row < size and 0 <= end_column < len(grid[0])):
                    continue
                if all(
                    grid[row + row_step * index][column + column_step * index] == letter
                    for index, letter in enumerate(word)
                ):
                    return True
    return False


# -- word bank ----------------------------------------------------------


@pytest.mark.parametrize(
    "phrase, expected",
    [
        ("the big Bedouin hospitality tent", "HOSPITALITY"),
        ("date palms", "PALMS"),
        ("camels", "CAMELS"),
        ("a boat trip", "BOAT"),
        ("the", None),
        ("of a", None),
    ],
)
def test_puzzle_word_extraction(phrase, expected):
    assert puzzle_word(phrase, max_length=11) == expected


def test_puzzle_word_folds_accents():
    assert puzzle_word("Petrin funicular") == "FUNICULAR"
    assert puzzle_word("Český Krumlov") == "KRUMLOV"


def test_word_bank_mixes_categories(context):
    entries = build_word_bank(context, count=8, key="test")
    assert len({entry.category for entry in entries}) >= 3


def test_word_bank_rejects_near_duplicates():
    """CAMEL and CAMELS in one puzzle read as a mistake."""
    knowledge = DestinationKnowledge(
        wildlife=("camels", "camel calves"),
        landmarks=("the camel yard", "the lookout"),
        source="test",
    )
    context = WorkbookContext(destination="Testville", knowledge=knowledge)
    words = [entry.word for entry in build_word_bank(context, count=8, key="dupes")]
    assert len(words) == len(set(words))
    for word in words:
        assert not any(other != word and word in other for other in words)


def test_word_bank_is_deterministic(context):
    assert build_word_bank(context, count=6, key="k") == build_word_bank(
        context, count=6, key="k"
    )


def test_blanked_source_becomes_a_clue(context):
    entries = build_word_bank(context, count=12, key="clues")
    blanked = [entry.blanked_source() for entry in entries if " " in entry.source]
    assert blanked, "multi-word phrases should yield fill-in-the-blank clues"
    for clue in blanked:
        assert "___" in clue


# -- word search ---------------------------------------------------------


@pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS)
def test_every_listed_word_is_actually_in_the_grid(context, difficulty):
    draft = get_generator("word_search").generate(context, _slot("word_search", difficulty))
    grid = draft.metadata["grid"]
    words = draft.metadata["words"]

    assert words, "a word search needs words"
    for word in words:
        assert _find(grid, word), f"{word} is listed but not present in the grid"


@pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS)
def test_grid_is_square_and_fully_filled(context, difficulty):
    draft = get_generator("word_search").generate(context, _slot("word_search", difficulty))
    size = draft.metadata["grid_size"]
    grid = draft.metadata["grid"]

    assert len(grid) == size
    assert all(len(row) == size for row in grid)
    assert all(letter.isalpha() and letter.isupper() for row in grid for letter in row)


def test_placements_match_the_listed_words(context):
    draft = get_generator("word_search").generate(context, _slot("word_search"))
    placed = {placement["word"] for placement in draft.metadata["placements"]}
    assert placed == set(draft.metadata["words"])


def test_easy_word_search_has_no_diagonals_or_reversals(context):
    draft = get_generator("word_search").generate(context, _slot("word_search", "easy"))
    for placement in draft.metadata["placements"]:
        assert placement["direction"] in ([0, 1], [1, 0])


def test_word_search_needs_no_illustration(context):
    draft = get_generator("word_search").generate(context, _slot("word_search"))
    assert draft.metadata["needs_illustration"] is False
    prompt_text = " ".join(draft.image_brief.extra_constraints).lower()
    assert "do not draw a grid" in prompt_text


# -- crossword ------------------------------------------------------------


@pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS)
def test_every_answer_reads_correctly_in_the_solution(context, difficulty):
    draft = get_generator("crossword").generate(context, _slot("crossword", difficulty))
    meta = draft.metadata
    solution = meta["solution"]

    clues = meta["across"] + meta["down"]
    assert len(clues) >= 4
    for clue in clues:
        row, column = clue["row"], clue["column"]
        step = (0, 1) if clue in meta["across"] else (1, 0)
        letters = "".join(
            solution[row + step[0] * index][column + step[1] * index]
            for index in range(clue["length"])
        )
        assert letters == clue["answer"], f"{clue['answer']} does not read back from the grid"


def test_layout_and_solution_agree(context):
    meta = get_generator("crossword").generate(context, _slot("crossword")).metadata
    for layout_row, solution_row in zip(meta["layout"], meta["solution"]):
        for layout_cell, solution_cell in zip(layout_row, solution_row):
            assert (layout_cell == ".") == (solution_cell != "#")


def test_every_word_interlocks(context):
    """A crossword whose words don't cross is just a word list."""
    meta = get_generator("crossword").generate(context, _slot("crossword")).metadata
    across_cells = {
        (clue["row"], clue["column"] + index)
        for clue in meta["across"]
        for index in range(clue["length"])
    }
    down_cells = {
        (clue["row"] + index, clue["column"])
        for clue in meta["down"]
        for index in range(clue["length"])
    }
    assert across_cells & down_cells, "no across word crosses a down word"
    for clue in meta["down"]:
        cells = {(clue["row"] + i, clue["column"]) for i in range(clue["length"])}
        assert cells & across_cells, f"{clue['answer']} crosses nothing"


def test_clue_numbers_follow_reading_order(context):
    meta = get_generator("crossword").generate(context, _slot("crossword")).metadata
    numbers = meta["numbers"]
    ordered = sorted(numbers, key=lambda entry: (entry["row"], entry["column"]))
    assert [entry["number"] for entry in ordered] == list(range(1, len(ordered) + 1))

    numbered = {(entry["row"], entry["column"]): entry["number"] for entry in numbers}
    for clue in meta["across"] + meta["down"]:
        assert numbered[(clue["row"], clue["column"])] == clue["number"]


def test_clues_are_not_empty(context):
    meta = get_generator("crossword").generate(context, _slot("crossword")).metadata
    for clue in meta["across"] + meta["down"]:
        assert clue["clue"].strip()
        assert clue["answer"] not in clue["clue"], "the clue must not contain its answer"


def test_crossword_grid_stays_compact(context):
    """Sprawl makes the squares too small to write in."""
    meta = get_generator("crossword").generate(context, _slot("crossword", "hard")).metadata
    assert meta["columns"] <= 16
    assert meta["rows"] <= 16


def test_puzzles_are_unsupported_without_vocabulary():
    bare = WorkbookContext(
        destination="Nowhere",
        knowledge=DestinationKnowledge(history=("a long time ago",), source="test"),
    )
    assert not get_generator("word_search").supports(bare)
    assert not get_generator("crossword").supports(bare)


def test_puzzles_work_for_a_second_destination(builder):
    """Vocabulary must come from the destination, not a fixed list."""
    from src import generate_workbook

    desert = generate_workbook(destination="Kfar Hanokdim", write=False, builder=builder)
    city = generate_workbook(destination="Prague", write=False, builder=builder)

    def words(result):
        page = result.workbook.page_by_type("word_search")
        return set(page.metadata["words"]) if page else set()

    assert words(desert) and words(city)
    assert not words(desert) & words(city)
