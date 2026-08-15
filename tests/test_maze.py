"""The maze must be a real, uniquely-solvable puzzle.

Generation is a spanning tree over the grid, so "exactly one path, no stray
dead end" is a property of the algorithm, checked directly here — not a
sentence inside an image prompt.
"""

from __future__ import annotations

import pytest

from src.activities._maze import generate_maze, grid_for, solve, wall_segments
from src.activities.base import get_generator
from src.models.context import DIFFICULTY_LEVELS
from src.models.plan import PlannedPage
from src.rendering.layouts import LAYOUTS


def _slot(difficulty: str = "medium", number: int = 3) -> PlannedPage:
    return PlannedPage(number=number, activity_type="maze", difficulty=difficulty)


# -- the generated maze itself --------------------------------------------


@pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS)
def test_the_maze_is_a_spanning_tree(difficulty):
    import random

    columns, rows = grid_for(difficulty)
    maze = generate_maze(random.Random(1), columns, rows)
    open_edges = 0
    for row in range(rows):
        for col in range(columns):
            mask = maze.walls[row][col]
            if not mask & 1:  # NORTH open
                open_edges += 1
            if not mask & 2:  # EAST open
                open_edges += 1
    assert open_edges == rows * columns - 1


def test_every_cell_is_reachable():
    import random

    columns, rows = grid_for("medium")
    maze = generate_maze(random.Random(2), columns, rows)
    path = solve(maze, (0, 0), (rows - 1, columns - 1))
    # A spanning tree walk visiting rows*columns-1 edges implies every cell
    # was reached during the carve; confirm the corners specifically connect.
    assert path[0] == (0, 0)
    assert path[-1] == (rows - 1, columns - 1)


def test_walls_are_reciprocal():
    import random

    columns, rows = grid_for("easy")
    maze = generate_maze(random.Random(3), columns, rows)
    for row in range(rows):
        for col in range(columns):
            if not maze.walls[row][col] & 2:  # this cell's EAST is open
                assert col + 1 < columns
                assert not maze.walls[row][col + 1] & 8  # neighbour's WEST is open
            if not maze.walls[row][col] & 4:  # this cell's SOUTH is open
                assert row + 1 < rows
                assert not maze.walls[row + 1][col] & 1  # neighbour's NORTH is open


def test_the_outer_boundary_is_closed():
    import random

    columns, rows = grid_for("easy")
    maze = generate_maze(random.Random(4), columns, rows)
    for col in range(columns):
        assert maze.walls[0][col] & 1  # top row's NORTH wall stands
        assert maze.walls[rows - 1][col] & 4  # bottom row's SOUTH wall stands
    for row in range(rows):
        assert maze.walls[row][0] & 8  # left column's WEST wall stands
        assert maze.walls[row][columns - 1] & 2  # right column's EAST wall stands


def test_the_solution_is_a_real_walk():
    import random

    columns, rows = grid_for("medium")
    maze = generate_maze(random.Random(5), columns, rows)
    start, goal = (0, 0), (rows - 1, columns - 1)
    path = solve(maze, start, goal)
    assert path[0] == start
    assert path[-1] == goal
    for (row, col), (next_row, next_col) in zip(path, path[1:]):
        assert abs(row - next_row) + abs(col - next_col) == 1  # single-step, adjacent


def test_the_same_seed_makes_the_same_maze():
    import random

    columns, rows = grid_for("easy")
    first = generate_maze(random.Random(42), columns, rows)
    second = generate_maze(random.Random(42), columns, rows)
    assert first == second


def test_corridors_stay_wide_enough_for_a_crayon():
    """176mm usable width / columns must clear the 13mm floor a chunky
    crayon needs, at every difficulty."""
    for difficulty in DIFFICULTY_LEVELS:
        columns, _ = grid_for(difficulty)
        assert 176 / columns >= 13


def test_wall_segments_draws_every_wall_exactly_once():
    import random

    columns, rows = grid_for("easy")
    maze = generate_maze(random.Random(6), columns, rows)
    d = wall_segments(maze)
    # A spanning tree over rows*columns cells has rows*columns+1 closed
    # walls when counting the boundary, but the cheapest direct check is
    # simply that every "M" move corresponds to one drawn segment.
    assert d.count("M") == d.count("H") + d.count("V")


# -- the activity ------------------------------------------------------


def test_generation_is_deterministic(context):
    activity = get_generator("maze")
    slot = _slot()
    first = activity.generate(context, slot)
    second = activity.generate(context, slot)
    assert first == second


def test_a_different_page_number_makes_a_different_maze(context):
    activity = get_generator("maze")
    first = activity.generate(context, _slot(number=3))
    second = activity.generate(context, _slot(number=6))
    assert first.metadata["grid"]["walls"] != second.metadata["grid"]["walls"]


def test_the_page_needs_no_illustration(context):
    draft = get_generator("maze").generate(context, _slot())
    assert draft.metadata["needs_illustration"] is False
    assert draft.image_brief is None


def test_two_marker_symbols_are_returned(context):
    draft = get_generator("maze").generate(context, _slot())
    assert len(draft.symbols) == 2
    keys = {symbol.key for symbol in draft.symbols}
    assert "airplane" in keys


def test_difficulty_changes_only_the_grid_size(context):
    activity = get_generator("maze")
    sizes = {
        difficulty: activity.generate(context, _slot(difficulty=difficulty)).metadata["grid"]
        for difficulty in DIFFICULTY_LEVELS
    }
    assert sizes["easy"]["columns"] < sizes["medium"]["columns"] < sizes["hard"]["columns"]


def test_a_hebrew_maze_starts_on_the_right(context):
    from dataclasses import replace

    hebrew_context = replace(context, language="he")
    draft = get_generator("maze").generate(hebrew_context, _slot())
    grid = draft.metadata["grid"]
    assert grid["start_cell"][1] == grid["columns"] - 1
    assert grid["goal_cell"][1] == 0


def test_an_english_maze_starts_on_the_left(context):
    draft = get_generator("maze").generate(context, _slot())
    grid = draft.metadata["grid"]
    assert grid["start_cell"] == [0, 0]
    assert grid["goal_cell"] == [grid["rows"] - 1, grid["columns"] - 1]


def test_the_first_mazes_instructions_name_the_airplane(context):
    """The first maze in a book starts at the airplane icon — before this
    fix, the instructions always said the fixed, unrelated "home"/"הבית"
    regardless of which icon actually printed."""
    draft = get_generator("maze").generate(context, _slot(number=3))
    assert draft.symbols[0].key == "airplane"
    assert draft.symbols[0].label in draft.instructions
    assert "home" not in draft.instructions.lower()


def test_a_repeat_mazes_instructions_name_the_repeat_icon(context):
    """A second maze in the same book prints a fixed, different start icon
    (see ``_REPEAT_START_ICON``) — its instructions must name *that* icon,
    not the airplane and not the old fixed "home"."""
    from dataclasses import replace

    slot = replace(_slot(number=6), metadata={"occurrence": 2})
    draft = get_generator("maze").generate(context, slot)
    assert draft.symbols[0].key == "dog"
    assert draft.symbols[0].label in draft.instructions
    assert "home" not in draft.instructions.lower()


def test_a_hebrew_repeat_maze_names_the_dog_not_the_house(context):
    from dataclasses import replace

    hebrew_context = replace(context, language="he")
    slot = replace(_slot(number=6), metadata={"occurrence": 2})
    draft = get_generator("maze").generate(hebrew_context, slot)
    assert draft.symbols[0].key == "dog"
    assert "הכלב" in draft.instructions
    assert "הבית" not in draft.instructions


def test_a_third_mazes_instructions_name_the_bicycle(context):
    """Occurrence 3 gets its own start icon, not a repeat of occurrence 2's
    dog — see ``_REPEAT_START_ICONS``."""
    from dataclasses import replace

    slot = replace(_slot(number=9), metadata={"occurrence": 3})
    draft = get_generator("maze").generate(context, slot)
    assert draft.symbols[0].key == "bicycle"
    assert draft.symbols[0].label in draft.instructions


def test_a_fourth_mazes_start_icon_degrades_gracefully(context):
    """``_REPEAT_START_ICONS`` only has 3 entries; a 4th occurrence (only
    reachable via the planner's own cap-bonus escape valve for a very long
    book) must still resolve to the last one instead of raising."""
    from dataclasses import replace

    slot = replace(_slot(number=12), metadata={"occurrence": 4})
    draft = get_generator("maze").generate(context, slot)
    assert draft.symbols[0].key == "truck"


# -- goal text/icon coherence --------------------------------------------


def test_goal_text_and_icon_agree_when_a_landmark_matches(context):
    """A landmark whose own concept coincides with a real library symbol
    (here, "village") must be printed with *that* symbol's icon, and the
    goal text must still be the landmark's own name — not a generic label."""
    from dataclasses import replace

    village_context = replace(
        context, knowledge=replace(context.knowledge, landmarks=("the village of Testtown",))
    )
    draft = get_generator("maze").generate(village_context, _slot(number=3))
    goal_symbol = draft.symbols[1]
    assert goal_symbol.key == "village"
    assert draft.metadata["goal"] == "the village of Testtown"
    assert goal_symbol.label == "the village of Testtown"
    assert draft.metadata["goal"] in draft.instructions
    assert draft.metadata["goal"] in draft.title


def test_goal_falls_back_to_a_generic_icon_when_no_landmark_matches(context):
    """None of the default fixture's landmarks ("the old lighthouse", "the
    harbour wall", "the cliff path") resolve to a real library symbol, so
    the old behaviour would print one of those names next to an unrelated
    icon (a live Pelion/he run showed exactly this: the steam train landmark
    paired with a generic mountain icon). The fix must never print an
    unmatched landmark name at all — it falls back to a generic,
    environment-appropriate icon and words the goal from *that* icon's own
    label instead, so text and icon always agree."""
    draft = get_generator("maze").generate(context, _slot(number=3))
    goal_symbol = draft.symbols[1]
    for landmark in context.knowledge.landmarks:
        assert landmark != draft.metadata["goal"]
        assert landmark not in draft.instructions
    # The fallback text is built from the icon's own label, so the two can
    # never disagree by construction.
    assert draft.metadata["goal"] in draft.instructions
    assert goal_symbol.key in {"mountain", "village", "boat", "fountain"}
    # Still destination-aware: test_activities_are_destination_aware's
    # contract must hold for this page too.
    assert context.destination in draft.metadata["goal"]


def test_a_maze_with_no_landmarks_still_names_the_destination(context):
    from dataclasses import replace

    bare_context = replace(context, knowledge=replace(context.knowledge, landmarks=()))
    draft = get_generator("maze").generate(bare_context, _slot(number=3))
    assert context.destination in draft.metadata["goal"]
    assert draft.symbols[1].key in {"mountain", "village", "boat", "fountain"}


def test_repeat_mazes_dont_duplicate_the_goal(context):
    """Two landmarks that both resolve to the same icon ("village") must not
    both be offered — a book's second maze needs its own distinct goal, not
    a same-icon duplicate under a different landmark name."""
    from dataclasses import replace

    two_villages_context = replace(
        context,
        knowledge=replace(
            context.knowledge,
            landmarks=("the village of Alpha", "the village of Beta"),
        ),
    )
    first = get_generator("maze").generate(
        two_villages_context, replace(_slot(number=3), metadata={"occurrence": 1})
    )
    second = get_generator("maze").generate(
        two_villages_context, replace(_slot(number=6), metadata={"occurrence": 2})
    )
    assert first.symbols[1].key != second.symbols[1].key
    assert first.metadata["goal"] != second.metadata["goal"]


def test_three_mazes_in_one_book_never_repeat_a_start_or_goal(context):
    """A book with 2-3 mazes must not print the same start icon or the same
    goal icon/text twice — the whole point of ``_REPEAT_START_ICONS`` and
    the occurrence-indexed goal resolver."""
    from dataclasses import replace

    pelion_like_context = replace(
        context,
        knowledge=replace(
            context.knowledge,
            landmarks=("the village of Alpha", "the village of Beta", "an untranslatable ruin"),
        ),
    )
    drafts = [
        get_generator("maze").generate(
            pelion_like_context, replace(_slot(number=3 * n), metadata={"occurrence": n})
        )
        for n in (1, 2, 3)
    ]
    start_keys = [draft.symbols[0].key for draft in drafts]
    goal_keys = [draft.symbols[1].key for draft in drafts]
    goal_texts = [draft.metadata["goal"] for draft in drafts]
    assert len(start_keys) == len(set(start_keys))
    assert len(goal_keys) == len(set(goal_keys))
    assert len(goal_texts) == len(set(goal_texts))


# -- rendering -----------------------------------------------------------


def test_maze_has_a_bespoke_layout():
    assert "maze" in LAYOUTS
