"""Every activity plugin must honour the same contract."""

from __future__ import annotations

import pytest

from src.activities import load_activities
from src.activities.base import ACTIVITY_REGISTRY, available_activities, get_generator
from src.models.context import (
    DIFFICULTY_LEVELS,
    Child,
    DestinationKnowledge,
    WorkbookContext,
)
from src.models.page import ActivityDraft, RenderMode
from src.models.plan import PlannedPage

EXPECTED_ACTIVITIES = {
    "cover",
    "coloring",
    "maze",
    "spot_difference",
    "hidden_objects",
    "packing",
    "matching",
    "wildlife_facts",
    "quiz",
    "drawing",
    "reflection",
}


def test_all_activities_are_discovered():
    load_activities()
    assert EXPECTED_ACTIVITIES <= set(ACTIVITY_REGISTRY)


def test_registry_keys_match_their_class():
    for activity_type, cls in ACTIVITY_REGISTRY.items():
        assert cls.activity_type == activity_type


def test_loading_twice_is_idempotent():
    before = dict(load_activities())
    assert load_activities() == before


@pytest.mark.parametrize("activity", available_activities(), ids=lambda a: a.activity_type)
@pytest.mark.parametrize("difficulty", DIFFICULTY_LEVELS)
def test_generate_returns_a_complete_draft(context, activity, difficulty):
    planned = PlannedPage(
        number=3,
        activity_type=activity.activity_type,
        difficulty=difficulty,
        target_age=6,
        focus="wildlife",
    )
    draft = activity.generate(context, planned)

    assert isinstance(draft, ActivityDraft)
    assert draft.type == activity.activity_type
    assert draft.title.strip()
    assert draft.instructions.strip()
    assert draft.educational_goal.strip()
    assert draft.estimated_age.strip()

    brief = draft.image_brief
    assert brief.subject.strip()
    assert brief.render_mode in RenderMode.ALL
    assert all(element.strip() for element in brief.elements)


@pytest.mark.parametrize("activity", available_activities(), ids=lambda a: a.activity_type)
def test_generation_is_deterministic(context, activity, planned):
    slot = PlannedPage(number=4, activity_type=activity.activity_type, focus="landmarks")
    first = activity.generate(context, slot)
    second = activity.generate(context, slot)
    assert first == second


@pytest.mark.parametrize("activity", available_activities(), ids=lambda a: a.activity_type)
def test_activities_are_destination_aware(context, activity):
    """Content must come from the knowledge, not from a fixed script."""
    slot = PlannedPage(number=2, activity_type=activity.activity_type, focus="wildlife")
    draft = activity.generate(context, slot)
    haystack = " ".join(
        [draft.title, draft.instructions, draft.image_brief.subject, draft.image_brief.scene]
        + list(draft.image_brief.elements)
        + list(draft.image_brief.extra_constraints)
    ).lower()

    known = [
        value.lower()
        for name in ("landmarks", "wildlife", "plants", "activities", "local_food")
        for value in context.knowledge.get(name)
    ]
    assert context.destination.lower() in haystack or any(
        value in haystack for value in known
    )


def test_supports_rejects_activities_that_lack_their_knowledge():
    bare = WorkbookContext(destination="Nowhere", knowledge=DestinationKnowledge(source="test"))
    wildlife = get_generator("wildlife_facts")
    assert wildlife.required_knowledge == ("wildlife",)
    assert not wildlife.supports(bare)


def test_supports_respects_age_range(context):
    quiz = get_generator("quiz")
    assert quiz.supports(context)
    # A book for a single three-year-old has no business containing a quiz.
    toddler_only = WorkbookContext(
        destination=context.destination,
        knowledge=context.knowledge,
        children=(Child("Tal", 3),),
    )
    assert not quiz.supports(toddler_only)


def test_unknown_activity_type_is_a_clear_error():
    with pytest.raises(KeyError, match="unknown activity type"):
        get_generator("interpretive_dance")


def test_maze_records_a_single_solution_constraint(context):
    draft = get_generator("maze").generate(
        context, PlannedPage(number=3, activity_type="maze", difficulty="medium")
    )
    assert draft.metadata["start"] != draft.metadata["goal"]
    assert any("one correct route" in c for c in draft.image_brief.extra_constraints)


def test_quiz_answers_are_real_and_not_always_first(context):
    draft = get_generator("quiz").generate(
        context, PlannedPage(number=9, activity_type="quiz", difficulty="hard")
    )
    questions = draft.metadata["questions"]
    assert len(questions) >= 3
    for question in questions:
        assert question["answer"] in question["options"]
        assert question["answer"] in context.knowledge.get(question["category"])
        assert question["options"][question["answer_index"] - 1] == question["answer"]
    assert len({question["answer_index"] for question in questions}) > 1


def test_hidden_objects_count_matches_the_listed_items(context):
    draft = get_generator("hidden_objects").generate(
        context, PlannedPage(number=5, activity_type="hidden_objects", difficulty="hard")
    )
    objects = draft.metadata["objects"]
    assert len(objects) == draft.metadata["object_count"] == 10
    assert len(set(objects)) == len(objects)
    assert str(len(objects)) in draft.instructions


def test_packing_reacts_to_the_weather():
    hot = WorkbookContext(
        destination="Sunland",
        knowledge=DestinationKnowledge(
            weather=("hot and dry all day",), activities=("a desert hike",), source="test"
        ),
    )
    cold = WorkbookContext(
        destination="Snowland",
        knowledge=DestinationKnowledge(
            weather=("freezing and snowy",), activities=("a sledge ride",), source="test"
        ),
    )
    slot = PlannedPage(number=6, activity_type="packing", difficulty="medium")
    packing = get_generator("packing")
    hot_items = packing.generate(hot, slot).metadata["items"]
    cold_items = packing.generate(cold, slot).metadata["items"]

    assert "sun hat" in hot_items and "sun hat" not in cold_items
    assert "warm coat" in cold_items and "warm coat" not in hot_items


def test_matching_answer_key_is_consistent(context):
    draft = get_generator("matching").generate(
        context, PlannedPage(number=7, activity_type="matching", difficulty="medium")
    )
    left = draft.metadata["left_column"]
    right = draft.metadata["right_column"]
    assert sorted(left) == sorted(right)
    for subject, position in draft.metadata["answer_key"].items():
        assert right[position - 1] == subject
