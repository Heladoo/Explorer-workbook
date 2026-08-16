"""The planner decides order, difficulty and audience — and nothing else."""

from __future__ import annotations

import pytest

from src.activities.base import get_generator
from src.agents.planner import WorkbookPlanner
from src.models.context import DIFFICULTY_LEVELS, Child, DestinationKnowledge, WorkbookContext


def _with(context: WorkbookContext, **changes) -> WorkbookContext:
    from dataclasses import replace

    return replace(context, **changes)


def test_cover_opens_and_reflection_closes(context):
    plan = WorkbookPlanner().plan(context)
    assert plan[0].activity_type == "cover"
    assert plan[-1].activity_type == "reflection"


def test_page_numbers_are_contiguous(context):
    plan = WorkbookPlanner().plan(context)
    assert [page.number for page in plan] == list(range(1, len(plan) + 1))


@pytest.mark.parametrize("page_count", [3, 6, 12, 20, 30])
def test_page_count_is_honoured(context, page_count):
    plan = WorkbookPlanner().plan(_with(context, page_count=page_count))
    assert len(plan) == page_count


def test_below_minimum_page_count_is_raised_to_the_floor(context):
    plan = WorkbookPlanner().plan(_with(context, page_count=1))
    assert len(plan) == 3
    assert plan[0].activity_type == "cover"
    assert plan[-1].activity_type == "reflection"


def test_difficulty_never_goes_backwards_through_the_body(context):
    plan = WorkbookPlanner().plan(_with(context, page_count=14))
    body = [page for page in plan[1:-1]]
    levels = [DIFFICULTY_LEVELS.index(page.difficulty) for page in body]
    assert levels == sorted(levels)
    assert levels[0] < levels[-1], "the book should get harder as it goes"


def test_difficulty_is_capped_for_young_children(context):
    young = _with(context, children=(Child("Tal", 5),), page_count=12)
    plan = WorkbookPlanner().plan(young)
    assert {page.difficulty for page in plan} <= {"easy", "medium"}


def test_explicit_difficulty_overrides_the_ramp(context):
    plan = WorkbookPlanner().plan(_with(context, difficulty="hard", page_count=10))
    assert {page.difficulty for page in plan[1:-1]} == {"hard"}


def test_unknown_difficulty_is_rejected(context):
    with pytest.raises(ValueError, match="unknown difficulty"):
        WorkbookPlanner().plan(_with(context, difficulty="impossible"))


def test_target_ages_stay_within_the_family(context):
    plan = WorkbookPlanner().plan(context)
    for page in plan:
        assert context.min_age <= page.target_age <= context.max_age


def test_activities_alternate_between_quiet_and_active(context):
    plan = WorkbookPlanner().plan(_with(context, page_count=12))
    energies = [get_generator(page.activity_type).energy for page in plan[1:-1]]
    runs = max(_longest_run(energies), 1)
    assert runs <= 3, f"too many {energies} pages of the same energy in a row"


def test_interests_pull_matching_activities_into_the_book(context):
    # wildlife_facts and hidden_objects are currently paused (`enabled = False`),
    # so "animals" can only pull in the third favoured activity: matching.
    plain = WorkbookPlanner().plan(_with(context, page_count=6))
    animal_lover = WorkbookPlanner().plan(
        _with(context, page_count=6, interests=("animals",))
    )
    assert "matching" in [page.activity_type for page in animal_lover]
    assert plain != animal_lover


def test_focus_rotates_across_available_knowledge(context):
    plan = WorkbookPlanner().plan(_with(context, page_count=12))
    focuses = {page.focus for page in plan}
    assert len(focuses) >= 4
    assert None not in focuses


def test_itinerary_days_are_spread_over_the_body(context):
    plan = WorkbookPlanner().plan(_with(context, page_count=10))
    days = [page.itinerary_day for page in plan if page.itinerary_day]
    assert set(days) == set(context.trip.itinerary)


def test_unsupported_activities_are_left_out(context):
    """A destination with no wildlife cannot have a wildlife facts page."""
    knowledge = DestinationKnowledge(
        landmarks=("the old mill", "the water tower"),
        activities=("a walk along the canal",),
        local_food=("apple cake",),
        source="test",
    )
    plan = WorkbookPlanner().plan(_with(context, knowledge=knowledge, page_count=8))
    assert "wildlife_facts" not in [page.activity_type for page in plan]


def test_planner_accepts_an_injected_catalogue(context):
    only_coloring = WorkbookPlanner(
        [get_generator("cover"), get_generator("coloring"), get_generator("reflection")]
    )
    plan = only_coloring.plan(_with(context, page_count=6))
    assert [page.activity_type for page in plan] == [
        "cover",
        "coloring",
        "coloring",
        "coloring",
        "coloring",
        "reflection",
    ]


def test_planner_needs_something_to_plan_with(context):
    with pytest.raises(RuntimeError):
        WorkbookPlanner([get_generator("cover")]).plan(context)


def _longest_run(values: list[str]) -> int:
    longest = current = 1
    for previous, value in zip(values, values[1:]):
        current = current + 1 if value == previous else 1
        longest = max(longest, current)
    return longest
