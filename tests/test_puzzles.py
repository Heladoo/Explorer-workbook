"""The word search must be genuinely solvable.

This page carries no illustration — the puzzle *is* the data — so the tests
solve it rather than checking that fields are populated.
"""

from __future__ import annotations

import pytest

from src.activities._wordbank import build_word_bank, normalize, puzzle_word
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


def test_puzzle_word_admits_defeat_when_every_candidate_is_prefixed():
    """If *every* length-eligible token in a phrase carries a Hebrew
    proclitic, there is no safe word to use — before this fix, puzzle_word()
    fell back to using one anyway (a fragment like "בסירות"/"מפירות" instead
    of a real word). build_word_bank() already tolerates fewer than `count`
    words, so returning None here just means it moves on to a cleaner word
    from a different phrase."""
    # Every token here is a real word carrying one of the proclitic letters
    # (ו/ב/כ/ל/מ/ש/ה) as its first character, with nothing unprefixed left.
    assert puzzle_word("בסירות מפרשים") is None


def test_puzzle_word_still_prefers_an_unprefixed_candidate():
    """A phrase offering even one clean word must never fall back to a
    prefixed one — the existing, already-fixed half of this behaviour."""
    assert puzzle_word("סירות מפרשים") == normalize("סירות")


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
    assert draft.image_brief is None


def test_easy_instructions_never_mention_diagonal_placement(context):
    """``_DIRECTIONS["easy"]`` has no diagonal step at all, so its
    instructions must not claim one is possible."""
    draft = get_generator("word_search").generate(context, _slot("word_search", "easy"))
    assert "slant" not in draft.instructions.lower()
    assert "אלכסון" not in draft.instructions


def test_hard_instructions_do_mention_diagonal_placement(context):
    draft = get_generator("word_search").generate(context, _slot("word_search", "hard"))
    assert "slant" in draft.instructions.lower()


def test_hard_instructions_mention_diagonal_placement_in_hebrew(context):
    from dataclasses import replace

    hebrew_context = replace(context, language="he")
    draft = get_generator("word_search").generate(hebrew_context, _slot("word_search", "hard"))
    assert "אלכסון" in draft.instructions


def test_puzzles_are_unsupported_without_vocabulary():
    bare = WorkbookContext(
        destination="Nowhere",
        knowledge=DestinationKnowledge(history=("a long time ago",), source="test"),
    )
    assert not get_generator("word_search").supports(bare)


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
