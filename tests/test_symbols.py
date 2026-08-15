"""The faceted symbol library and destination profiles.

Phase 1/2 foundation only: a relevance *score* combining a symbol's facets
with a destination's profile is deliberately not built yet (see
``src/symbols/__init__.py``'s docstring) — these tests pin the data the
facets and profiles carry, and the loader's integrity guarantees, not any
weighting of them.
"""

from __future__ import annotations

import json
import random

import pytest

from src.models.context import DestinationKnowledge, DestinationProfile
from src.slug import slugify
from src.symbols import REQUIRED_KEYS, library, load_library, missing_art
from src.symbols.loader import LibraryError
from src.symbols.profile import derive_profile, profile_for
from src.symbols.vocab import CLIMATES, ENVIRONMENTS, REGIONS, ROLES, STATUS, TOPICS, UBIQUITY

# -- library integrity -----------------------------------------------------


def test_the_default_library_loads():
    assert len(library().all()) > 0


def test_every_key_is_unique():
    keys = [symbol.key for symbol in library().all()]
    assert len(keys) == len(set(keys))


def test_every_key_is_already_a_slug():
    for symbol in library().all():
        assert slugify(symbol.key) == symbol.key, symbol.key


def test_every_required_key_is_present():
    """``maze.py`` names ``airplane`` by hand rather than sampling; removing
    it from the library must fail here, not crash a book at generation."""
    present = {symbol.key for symbol in library().all()}
    for key in REQUIRED_KEYS:
        assert key in present, key


def test_every_facet_uses_the_closed_vocabulary():
    for symbol in library().all():
        facets = symbol.facets
        assert facets is not None
        assert facets.topic in TOPICS, symbol.key
        assert facets.ubiquity in UBIQUITY, symbol.key
        assert facets.status in STATUS, symbol.key
        assert set(facets.environments) <= set(ENVIRONMENTS), symbol.key
        assert set(facets.climate) <= set(CLIMATES), symbol.key
        assert set(facets.regions) <= set(REGIONS), symbol.key
        assert set(facets.roles) <= set(ROLES), symbol.key


def test_no_alias_collides_with_a_real_key():
    keys = {symbol.key for symbol in library().all()}
    for symbol in library().all():
        for alias in symbol.facets.aliases:
            assert alias not in keys, (symbol.key, alias)


def test_no_alias_is_claimed_twice():
    claimed: dict[str, str] = {}
    for symbol in library().all():
        for alias in symbol.facets.aliases:
            assert alias not in claimed, (alias, claimed.get(alias), symbol.key)
            claimed[alias] = symbol.key


def test_missing_art_is_exactly_the_draft_entries():
    assert set(missing_art()) == {
        symbol.key for symbol in library().all() if symbol.facets.status == "draft"
    }


def test_the_universal_pool_stays_within_the_full_library():
    pool_keys = {symbol.key for symbol in library().universal_pool()}
    all_keys = {symbol.key for symbol in library().all()}
    assert pool_keys <= all_keys


# -- malformed input, hand-rolled ------------------------------------------


def _entry(key: str, **overrides) -> dict:
    base = {
        "key": key,
        "label": f"a {key}",
        "subject": f"a {key}",
        "topic": "street",
        "ubiquity": "everywhere",
        "status": "ready",
    }
    base.update(overrides)
    return base


def _write(path, *symbols) -> None:
    path.write_text(json.dumps({"symbols": list(symbols)}), encoding="utf-8")


def test_a_bad_tag_raises_rather_than_being_silently_dropped(tmp_path):
    """Unlike a destination pack, the library is first-party structure — a
    misspelt tag here must fail loudly, not silently change what every book
    picks."""
    path = tmp_path / "library.json"
    _write(path, _entry("airplane", environments=["not-a-real-environment"]))
    with pytest.raises(LibraryError):
        load_library(path)


def test_an_unknown_field_raises(tmp_path):
    path = tmp_path / "library.json"
    _write(path, _entry("airplane", enviroments=["water"]))  # typo'd field name
    with pytest.raises(LibraryError):
        load_library(path)


def test_a_missing_required_field_raises(tmp_path):
    path = tmp_path / "library.json"
    entry = _entry("airplane")
    del entry["subject"]
    _write(path, entry)
    with pytest.raises(LibraryError):
        load_library(path)


def test_a_key_that_is_not_already_a_slug_raises(tmp_path):
    path = tmp_path / "library.json"
    _write(path, _entry("Not A Slug"))
    with pytest.raises(LibraryError):
        load_library(path)


def test_a_duplicate_key_in_one_file_raises(tmp_path):
    path = tmp_path / "library.json"
    _write(path, _entry("airplane"), _entry("airplane"))
    with pytest.raises(LibraryError):
        load_library(path)


def test_a_library_missing_a_required_key_raises(tmp_path):
    path = tmp_path / "library.json"
    _write(path, _entry("something-else"))
    with pytest.raises(LibraryError):
        load_library(path)


def test_a_colliding_alias_raises(tmp_path):
    path = tmp_path / "library.json"
    _write(
        path,
        _entry("airplane"),
        _entry("flag"),
        _entry("boat", aliases=["airplane"]),  # collides with a real key
    )
    with pytest.raises(LibraryError):
        load_library(path)


def test_loading_a_directory_merges_every_json_file(tmp_path):
    _write(tmp_path / "a.json", _entry("airplane"))
    _write(tmp_path / "b.json", _entry("flag"))
    lib = load_library(tmp_path)
    assert {symbol.key for symbol in lib.all()} == {"airplane", "flag"}


def test_a_key_repeated_across_two_files_in_a_directory_raises(tmp_path):
    _write(tmp_path / "a.json", _entry("airplane"), _entry("flag"))
    _write(tmp_path / "b.json", _entry("airplane"))
    with pytest.raises(LibraryError):
        load_library(tmp_path)


# -- order stability --------------------------------------------------------


def test_the_universal_pool_order_matches_the_historical_tuple():
    """``scavenger_hunt``/``matching`` build a dict from this pool and sample
    by population order, so reordering ``data/symbols/library.json`` would
    silently reshuffle every existing book's output even though no *content*
    changed. Pinning the order here, not just the set, is what catches that
    before it ships — see ``_symbols.py``'s "why output stays byte-identical"
    note."""
    from src.activities._symbols import UNIVERSAL_SYMBOLS

    assert [symbol.key for symbol in UNIVERSAL_SYMBOLS] == [
        "stop-sign", "police-car", "bicycle", "truck", "taxi", "tractor", "train",
        "bridge", "fountain", "flag", "house", "dog", "pigeon", "butterfly", "insect",
        "boat", "fish", "man-with-mustache", "ice-cream", "umbrella", "sunglasses", "airplane",
        "owl", "swallows-nesting", "goat", "kestrel", "squirrel", "swan", "fox",
        "horse", "cow", "eagle", "turtle", "donkey",
        "water-bottle", "baseball-cap", "binoculars", "rain-coat", "sunscreen",
        "hiking-shoes", "flip-flops", "gloves", "woolly-hat", "honey", "backpack",
    ]


def test_shuffling_the_source_file_does_not_change_any_entrys_content(tmp_path):
    """A future shard migration (splitting into per-topic files) must not
    silently corrupt or drop an entry, even though which *order* the
    resulting pool prints in is a separate guarantee (pinned above, and out
    of this test's scope — it belongs to the consumers that sample from it,
    not to the loader)."""
    from src.symbols import DEFAULT_LIBRARY_PATH

    payload = json.loads(DEFAULT_LIBRARY_PATH.read_text(encoding="utf-8"))
    shuffled_rows = list(payload["symbols"])
    random.Random(0).shuffle(shuffled_rows)
    path = tmp_path / "library.json"
    path.write_text(json.dumps({"symbols": shuffled_rows}), encoding="utf-8")

    shuffled = load_library(path)
    original_lib = library()

    assert {symbol.key for symbol in shuffled.all()} == {
        symbol.key for symbol in original_lib.all()
    }
    for symbol in original_lib.all():
        again = shuffled[symbol.key]
        assert again.label == symbol.label
        assert again.subject == symbol.subject
        assert again.facets == symbol.facets


# -- destination profiles ---------------------------------------------------


def test_every_packs_profile_uses_only_vocabulary_tags():
    from src.agents.destination_agent import DEFAULT_DATA_DIR

    for path in sorted(DEFAULT_DATA_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        block = data.get("profile")
        if not block:
            continue
        profile = DestinationProfile.from_dict(block)
        assert set(profile.regions) <= set(REGIONS), path.name
        assert set(profile.environments) <= set(ENVIRONMENTS), path.name
        assert set(profile.climate) <= set(CLIMATES), path.name


def test_translation_fragments_never_declare_their_own_profile():
    """``profile`` is structure, single-sourced in the base pack — a
    fragment (``<slug>.<lang>.json``) duplicating it would be exactly the
    hand-synced-by-two-people drift this file layout exists to avoid."""
    from src.agents.destination_agent import DEFAULT_DATA_DIR

    for path in sorted(DEFAULT_DATA_DIR.glob("*.json")):
        if "." not in path.stem:  # a base pack, not a translation fragment
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "profile" not in data, path.name


def test_a_translated_destination_resolves_to_the_base_packs_profile():
    """Resolving through a language fragment must not lose or alter the
    base pack's profile — ``_merge_translation`` never touches it."""
    from src.agents.destination_agent import FileKnowledgeProvider
    from tests.conftest import DATA_DIR

    provider = FileKnowledgeProvider(DATA_DIR)
    for destination in ("Kfar Hanokdim", "Pelion"):
        english = provider.fetch(destination, language="en")
        translated = provider.fetch(destination, language="he")
        assert translated.profile == english.profile
        assert translated.profile is not None


def test_an_authored_profile_is_used_as_is():
    authored = DestinationProfile(regions=("greece",), environments=("mountain",), source="authored")
    knowledge = DestinationKnowledge(source="test", profile=authored)
    assert profile_for(knowledge) is authored


def test_a_knowledge_only_destination_derives_a_profile(knowledge):
    """The ``knowledge`` fixture (Lighthouse Point) has no pack and no
    authored profile at all — ``profile_for`` must still return something
    usable, marked as a guess rather than a fact."""
    resolved = profile_for(knowledge)
    assert resolved.source == "derived"


def test_a_derived_profile_picks_up_coastal_language(knowledge):
    """The fixture's own knowledge text ("the harbour wall", "grey seals",
    "a boat trip") should surface a coastal environment without anyone
    authoring one by hand."""
    derived = derive_profile(knowledge)
    assert "coast" in derived.environments or "water" in derived.environments


def test_a_derived_profile_never_claims_authored_source():
    empty = DestinationKnowledge(source="test")
    assert derive_profile(empty).source == "derived"


# -- the brief's worked example, at the factor level ------------------------

#: Pelion's authored profile, duplicated here rather than read from the pack
#: so this test pins the *intended* shape independently of any future edit to
#: data/destinations/pelion.json.
_PELION = DestinationProfile(
    regions=("greece", "mediterranean", "europe"),
    environments=("mountain", "forest", "coast", "water", "village"),
    climate=("temperate", "hot"),
    source="authored",
)


def test_pelion_matches_greek_food_and_excludes_snow_gear():
    """The brief's worked example, at the *factor* level: souvlaki shares a
    region with Pelion, boat shares an environment, and skis-and-poles needs
    terrain Pelion has none of — exactly what a later scoring formula will
    read (see src/symbols/__init__.py's docstring for why the formula itself
    is deferred)."""
    lib = library()

    assert set(lib["souvlaki"].facets.regions) & set(_PELION.regions)
    assert set(lib["boat"].facets.environments) & set(_PELION.environments)
    assert not set(lib["skis-and-poles"].facets.environments) & set(_PELION.environments)
    assert not lib["umbrella"].facets.regions  # generic: nothing to match on


def test_the_real_pelion_pack_matches_the_pinned_profile():
    from src.agents.destination_agent import DEFAULT_DATA_DIR

    data = json.loads((DEFAULT_DATA_DIR / "pelion.json").read_text(encoding="utf-8"))
    profile = DestinationProfile.from_dict(data["profile"])
    assert set(profile.regions) == set(_PELION.regions)
    assert set(profile.environments) == set(_PELION.environments)
