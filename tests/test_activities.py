"""Every activity plugin must honour the same contract."""

from __future__ import annotations

import pytest

from src.activities import load_activities
from src.activities.base import ACTIVITY_REGISTRY, available_activities, get_generator
from src.models.context import (
    DIFFICULTY_LEVELS,
    Child,
    DestinationKnowledge,
    DestinationProfile,
    WorkbookContext,
)
from src.models.page import ActivityDraft, RenderMode
from src.models.plan import PlannedPage
from src.symbols import library

EXPECTED_ACTIVITIES = {
    "cover",
    "coloring",
    "maze",
    "spot_difference",
    "hidden_objects",
    "scavenger_hunt",
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
    if brief is None:
        assert draft.metadata.get("needs_illustration") is False
    else:
        assert brief.subject.strip()
        assert brief.render_mode in RenderMode.ALL
        assert all(element.strip() for element in brief.elements)


@pytest.mark.parametrize("activity", available_activities(), ids=lambda a: a.activity_type)
def test_generation_is_deterministic(context, activity, planned):
    slot = PlannedPage(number=4, activity_type=activity.activity_type, focus="landmarks")
    first = activity.generate(context, slot)
    second = activity.generate(context, slot)
    assert first == second


#: Pages whose content is deliberately not drawn from the destination's own
#: knowledge. ``matching`` is a shape-recognition puzzle: the child matches a
#: drawing to its silhouette, and the two have to be the same shape at the
#: same size, which only holds when both are derived from one cached drawing
#: (see ``src/activities/matching.py``) — a destination sight that has never
#: been drawn would print as a blank in the shadow column, so it draws from
#: the universal symbol bank instead. ``drawing`` is a blank frame with one
#: constant, general prompt in every book of a given language, by design
#: (see ``src/activities/drawing.py``) — naming a specific destination sight
#: would be exactly the "specific sub title" this page deliberately dropped.
DESTINATION_AGNOSTIC_ACTIVITIES = {"matching", "drawing"}


@pytest.mark.parametrize("activity", available_activities(), ids=lambda a: a.activity_type)
def test_activities_are_destination_aware(context, activity):
    """Content must come from the knowledge, not from a fixed script."""
    if activity.activity_type in DESTINATION_AGNOSTIC_ACTIVITIES:
        pytest.skip(f"{activity.activity_type} is deliberately destination-agnostic")
    slot = PlannedPage(number=2, activity_type=activity.activity_type, focus="wildlife")
    draft = activity.generate(context, slot)
    parts = [draft.title, draft.instructions]
    if draft.image_brief is not None:
        parts.extend(
            [draft.image_brief.subject, draft.image_brief.scene]
            + list(draft.image_brief.elements)
            + list(draft.image_brief.extra_constraints)
        )
    haystack = " ".join(parts).lower()

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


def test_maze_records_start_and_goal(context):
    draft = get_generator("maze").generate(
        context, PlannedPage(number=3, activity_type="maze", difficulty="medium")
    )
    assert draft.metadata["start"] != draft.metadata["goal"]
    assert draft.metadata["needs_illustration"] is False
    assert draft.image_brief is None
    assert len(draft.symbols) == 2


def test_drawing_instructions_are_constant_and_not_tied_to_a_specific_subject(context):
    """No {subject} is picked from the destination's knowledge — the page is a
    blank frame with one general prompt, the same in every book of a given
    language (see src/locales/*.py: drawing.instructions)."""
    first = get_generator("drawing").generate(
        context, PlannedPage(number=8, activity_type="drawing", difficulty="medium")
    )
    second = get_generator("drawing").generate(
        context, PlannedPage(number=10, activity_type="drawing", difficulty="hard")
    )
    assert first.instructions == second.instructions
    assert "prompt_subject" not in first.metadata


def test_quiz_answers_are_real_and_not_always_first(context):
    from src.activities._symbols import _topic

    draft = get_generator("quiz").generate(
        context, PlannedPage(number=9, activity_type="quiz", difficulty="hard")
    )
    questions = draft.metadata["questions"]
    assert len(questions) >= 3
    for question in questions:
        assert question["answer"] in question["options"]
        assert question["options"][question["answer_index"] - 1] == question["answer"]
        if question["category"]:
            # A knowledge-backed answer is shortened to its topic (see
            # src/activities/_symbols.py::_topic, used to keep a long
            # knowledge phrase from wrapping across a text quiz option) —
            # so it is never the raw pool entry verbatim, but it must still
            # be a genuine shortening of one, never invented.
            pool = context.knowledge.get(question["category"])
            assert any(_topic(item) == question["answer"] for item in pool)
        else:
            # A country-fact question (no fixture country here, but this
            # keeps the assertion honest if one is ever added) must still
            # answer with real, non-empty display text.
            assert question["answer"].strip()
    assert len({question["answer_index"] for question in questions}) > 1


def test_hidden_objects_count_matches_the_listed_items(context):
    draft = get_generator("hidden_objects").generate(
        context, PlannedPage(number=5, activity_type="hidden_objects", difficulty="hard")
    )
    objects = draft.metadata["objects"]
    assert len(objects) == draft.metadata["object_count"] == 10
    assert len(set(objects)) == len(objects)
    assert str(len(objects)) in draft.instructions


def test_scavenger_hunt_items_are_unique_and_counted(context):
    draft = get_generator("scavenger_hunt").generate(
        context, PlannedPage(number=5, activity_type="scavenger_hunt", difficulty="hard")
    )
    items = draft.metadata["items"]
    assert 16 <= len(items) <= 20
    assert len(items) == draft.metadata["item_count"]
    assert len(set(items)) == len(items)
    assert str(len(items)) in draft.instructions


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
    hot_keys = packing.generate(hot, slot).metadata["pack_keys"]
    cold_keys = packing.generate(cold, slot).metadata["pack_keys"]

    assert "baseball-cap" in hot_keys and "baseball-cap" not in cold_keys
    assert "woolly-hat" in cold_keys and "woolly-hat" not in hot_keys


def test_packing_flags_climate_wrong_gear_as_something_not_to_pack():
    """The literal case the page is meant to teach: a winter coat (or skis)
    doesn't belong on a desert trip, and the page should offer it as one of
    the things *not* to connect to the backpack rather than leave it out."""
    desert = WorkbookContext(
        destination="Sunland",
        knowledge=DestinationKnowledge(
            weather=("hot and dry all day",), activities=("a desert hike",), source="test"
        ),
    )
    slot = PlannedPage(number=6, activity_type="packing", difficulty="hard")
    draft = get_generator("packing").generate(desert, slot)
    pack_keys = set(draft.metadata["pack_keys"])
    distractor_keys = set(draft.metadata["distractor_keys"])

    assert pack_keys.isdisjoint(distractor_keys)
    assert distractor_keys
    assert {"winter-coat", "skis-and-poles", "gloves", "woolly-hat"} & distractor_keys


def test_packing_silly_distractors_are_portable_not_landscape():
    """The silly-pool fallback must never offer a landscape/structure item
    (a fountain, a bridge, a mountain) as something a child might mistake for
    packable — a live Pelion book shipped exactly that, which fails the
    page's actual test ("would a child mistakenly think to pack this?").

    A desert trip that matches *both* "hot" and "cold" keywords (a real
    desert's cold nights) is the concrete case that forces the whole
    distractor count onto the silly pool alone — see
    ``PackingActivity._distractor_symbols``: matching both climates leaves
    ``wrong_climates`` empty, so the climate-mismatch pool contributes
    nothing at all.
    """
    desert_with_cold_nights = WorkbookContext(
        destination="Sunland",
        knowledge=DestinationKnowledge(
            weather=("scorching hot by day", "freezing cold at night"),
            activities=("a desert hike",),
            source="test",
        ),
    )
    slot = PlannedPage(number=6, activity_type="packing", difficulty="hard")
    draft = get_generator("packing").generate(desert_with_cold_nights, slot)
    assert {"hot", "cold"} <= set(draft.metadata["matched_conditions"])

    non_portable_topics = {"buildings", "street", "nature", "water", "people"}
    lib = library()
    for key in draft.metadata["distractor_keys"]:
        symbol = lib[key]
        assert symbol.facets.topic not in non_portable_topics, (
            f"{key!r} (topic={symbol.facets.topic!r}) is not a portable, "
            "packable-scale object"
        )


def test_packing_distractor_pool_is_adequate_when_climate_matches_both():
    """The concrete regression this fix guards: restricting the silly pool
    to ``UNIVERSAL_SYMBOLS``' "everywhere"/"common" food entries left only 2
    items (ice-cream, honey) — one short of what "hard" wants (3) — whenever
    the climate-mismatch pool is empty (see the test above). Querying the
    whole library's ready "food" entries instead (5 items: also souvlaki,
    pasta, pomegranate) fixes it; this pins the count so a future change
    can't silently reintroduce the shortfall."""
    desert_with_cold_nights = WorkbookContext(
        destination="Sunland",
        knowledge=DestinationKnowledge(
            weather=("scorching hot by day", "freezing cold at night"),
            activities=("a desert hike",),
            source="test",
        ),
    )
    slot = PlannedPage(number=6, activity_type="packing", difficulty="hard")
    draft = get_generator("packing").generate(desert_with_cold_nights, slot)
    assert len(draft.metadata["distractor_keys"]) == 3


def test_packing_silly_distractors_respect_the_destinations_own_region():
    """A live Kfar Hanokdim (Israel) book offered Greek souvlaki and a bowl
    of pasta as things not to pack — both carry a ``regions`` tag
    (``greece``; ``mediterranean``, ``europe``) that shares nothing with the
    destination's own authored profile (``israel``, ``middle-east``), which
    undermines the page's premise ("would you plausibly have considered
    bringing this?") for a trip that never mentioned either. The pool should
    prefer region-neutral food (ice-cream, honey) or food matching the
    destination's own region (pomegranate: also "middle-east") over an
    unrelated region's food, whenever there's enough to fill the count
    without it.
    """
    desert_with_cold_nights = WorkbookContext(
        destination="Kfar Hanokdim",
        knowledge=DestinationKnowledge(
            weather=("scorching hot by day", "freezing cold at night"),
            activities=("a desert hike",),
            source="test",
            profile=DestinationProfile(
                regions=("israel", "middle-east"), environments=("desert",), climate=("hot", "dry")
            ),
        ),
    )
    slot = PlannedPage(number=6, activity_type="packing", difficulty="hard")
    draft = get_generator("packing").generate(desert_with_cold_nights, slot)
    distractor_keys = set(draft.metadata["distractor_keys"])

    assert len(distractor_keys) == 3
    assert distractor_keys.isdisjoint({"souvlaki", "pasta"})


def test_packing_offers_a_library_symbol_only_where_the_terrain_fits():
    """``skis-and-poles`` only belongs in the *pack* pool for a destination
    whose own profile has the terrain for it, not merely a cold one (see the
    symbol library's veto rule, ``src/activities/packing.py``'s
    ``_pack_symbols``)."""
    snowy = WorkbookContext(
        destination="Snowland",
        knowledge=DestinationKnowledge(
            weather=("freezing and snowy",), activities=("a sledge ride",), source="test"
        ),
    )
    cold_not_snowy = WorkbookContext(
        destination="Desertville",
        knowledge=DestinationKnowledge(
            weather=("cold desert nights", "hot dry days"),
            activities=("a desert hike",),
            source="test",
        ),
    )
    slot = PlannedPage(number=6, activity_type="packing", difficulty="hard")
    packing = get_generator("packing")
    snowy_keys = packing.generate(snowy, slot).metadata["pack_keys"]
    desert_keys = packing.generate(cold_not_snowy, slot).metadata["pack_keys"]

    assert "skis-and-poles" in snowy_keys
    assert "skis-and-poles" not in desert_keys


def test_packing_is_symbol_backed_with_a_backpack_hub_and_no_duplicates():
    """The whole point of the redesign: no free-text items, one small drawing
    per thing, and the backpack itself is always the first symbol (the hub
    the print layout puts at the centre of the ring)."""
    context = WorkbookContext(
        destination="Sunland",
        knowledge=DestinationKnowledge(
            weather=("hot and dry all day",), activities=("a desert hike",), source="test"
        ),
    )
    slot = PlannedPage(number=6, activity_type="packing", difficulty="hard")
    draft = get_generator("packing").generate(context, slot)

    assert draft.symbols[0].key == "backpack" == draft.metadata["backpack_key"]
    ring_keys = [symbol.key for symbol in draft.symbols[1:]]
    assert ring_keys == draft.metadata["ring_keys"]
    assert len(ring_keys) == len(set(ring_keys))
    assert set(ring_keys) == set(draft.metadata["pack_keys"]) | set(draft.metadata["distractor_keys"])


def test_matching_answer_key_is_consistent(context):
    draft = get_generator("matching").generate(
        context, PlannedPage(number=7, activity_type="matching", difficulty="medium")
    )
    left = draft.metadata["left_column"]
    right = draft.metadata["right_column"]
    assert sorted(left) == sorted(right)
    for subject, position in draft.metadata["answer_key"].items():
        assert right[position - 1] == subject


def test_matching_symbol_fit_vetoes_on_the_facet_it_actually_declares():
    """Unit-level check of the veto rule itself (src/activities/matching.py),
    same shape as the one src/activities/packing.py already applies to its
    own pool. An empty environments/climate facet is "findable/relevant
    anywhere" (see SymbolFacets) and always passes."""
    from src.activities.matching import _fits

    woolly_hat = library()["woolly-hat"]
    boat = library()["boat"]

    hot = DestinationProfile(environments=("mountain", "village"), climate=("hot",))
    cold = DestinationProfile(environments=("mountain",), climate=("cold",))
    landlocked = DestinationProfile(environments=("mountain", "forest"), climate=())
    coastal = DestinationProfile(environments=("coast", "water"), climate=())

    assert not _fits(woolly_hat, hot), "a cold-only symbol must not fit a hot-only profile"
    assert _fits(woolly_hat, cold)
    assert not _fits(boat, landlocked), "a water-only symbol must not fit a landlocked profile"
    assert _fits(boat, coastal)


def test_matching_never_offers_a_climate_mismatched_symbol():
    """Integration-level check: a warm-climate destination's matching page
    must never draw a woolly hat or gloves, across every difficulty and a
    wide spread of page numbers (context.sample's RNG key) — not just true
    on average. This is a hard guarantee, not a probabilistic one: Pelion's
    real profile leaves comfortably more than six climate-fitting universal
    symbols, so _choose's fitting pool never has to fall back to the
    unfiltered bank (see _choose's docstring)."""
    warm = WorkbookContext(
        destination="Sunland",
        knowledge=DestinationKnowledge(
            weather=("hot and sunny all summer",),
            activities=("a swim",),
            source="test",
            profile=DestinationProfile(
                environments=("mountain", "village", "coast"), climate=("hot", "temperate")
            ),
        ),
    )
    matching = get_generator("matching")
    for number in range(2, 30):
        for difficulty in DIFFICULTY_LEVELS:
            draft = matching.generate(
                warm, PlannedPage(number=number, activity_type="matching", difficulty=difficulty)
            )
            keys = draft.metadata["symbol_keys"]
            assert "woolly-hat" not in keys
            assert "gloves" not in keys


def test_matching_still_fills_every_pair_when_the_profile_is_sparse():
    """The fit filter must never leave the page short of pairs. A destination
    with no knowledge text derives an empty profile, which vetoes every
    climate/environment-tagged symbol in the pool — the 24 fully
    unconstrained symbols left are comfortably more than the largest pair
    count, so this doesn't even need _choose's unfiltered-bank fallback to
    pass; it is the fallback existing as a defensive floor beneath that, for
    whatever destination someday has an even thinner pool to draw from."""
    bare = WorkbookContext(
        destination="Nowhereland", knowledge=DestinationKnowledge(source="test")
    )
    for difficulty in DIFFICULTY_LEVELS:
        draft = get_generator("matching").generate(
            bare, PlannedPage(number=9, activity_type="matching", difficulty=difficulty)
        )
        assert len(draft.symbols) == len(draft.metadata["symbol_keys"])
        assert len(draft.metadata["symbol_keys"]) == len(set(draft.metadata["symbol_keys"]))
