"""Hebrew end to end: translated copy, RTL layout, English prompts."""

from __future__ import annotations

import json
import re

import pytest

from src import generate_workbook
from src.activities._wordbank import normalize, puzzle_word
from src.agents.destination_agent import FileKnowledgeProvider
from src.rendering.html_renderer import HtmlRenderer
from src.strings import available_languages, strings_for

from tests.conftest import DATA_DIR

HEBREW = re.compile(r"[֐-׿]")


@pytest.fixture
def hebrew(builder):
    return generate_workbook(
        destination="Kfar Hanokdim",
        children=["נעה", "עמית"],
        ages=[7, 9],
        language="he",
        page_count=12,
        write=False,
        builder=builder,
    )


# -- locale plumbing -----------------------------------------------------


def test_hebrew_locale_is_discovered():
    assert "he" in available_languages()
    assert strings_for("he").language == "he"
    assert strings_for("he-IL").language == "he", "region subtags resolve to the base locale"


def test_hebrew_is_right_to_left():
    assert strings_for("he").is_rtl
    assert not strings_for("en").is_rtl


def test_every_english_key_exists_in_hebrew():
    english = strings_for("en").table
    hebrew = strings_for("he").table
    missing = sorted(set(english) - set(hebrew))
    assert not missing, f"Hebrew locale is missing: {missing}"


def test_list_joining_follows_the_locale():
    assert strings_for("en").join(["Noa", "Amit"]) == "Noa and Amit"
    # Hebrew attaches the conjunction to the following word.
    assert strings_for("he").join(["נעה", "עמית"]) == "נעה ועמית"


# -- the pack ------------------------------------------------------------


def test_hebrew_pack_is_preferred_for_hebrew():
    provider = FileKnowledgeProvider(DATA_DIR)
    english = provider.fetch("Kfar Hanokdim", language="en")
    hebrew = provider.fetch("Kfar Hanokdim", language="he")

    assert not HEBREW.search(" ".join(english.wildlife))
    assert HEBREW.search(" ".join(hebrew.wildlife))
    assert hebrew.display_name == "כפר הנוקדים"


def test_missing_translation_falls_back_to_the_base_pack():
    provider = FileKnowledgeProvider(DATA_DIR)
    prague = provider.fetch("Prague", language="he")
    assert prague is not None
    assert "Charles Bridge" in prague.landmarks


def test_pack_languages_are_reported():
    provider = FileKnowledgeProvider(DATA_DIR)
    assert set(provider.languages_for("Kfar Hanokdim")) == {"en", "he"}
    assert provider.languages_for("Prague") == ("en",)


def test_translated_packs_are_one_destination():
    """A translation must not show up as a second destination."""
    known = FileKnowledgeProvider(DATA_DIR).known_destinations()
    assert len(known) == len(set(known))
    assert known.count("Kfar Hanokdim") == 1


def test_every_visual_entry_has_an_english_term():
    """Without this the image prompt would carry Hebrew nouns."""
    pack = json.loads((DATA_DIR / "kfar-hanokdim.he.json").read_text(encoding="utf-8"))
    terms = pack["illustration_terms"]
    for category in ("landmarks", "wildlife", "plants", "activities", "local_food"):
        for entry in pack[category]:
            assert entry in terms, f"{entry} has no English term for the prompt"
    assert not any(HEBREW.search(english) for english in terms.values())


# -- generated workbook ---------------------------------------------------


def test_page_copy_is_hebrew(hebrew):
    workbook = hebrew.workbook
    assert workbook.language == "he"
    assert HEBREW.search(workbook.title)
    assert "כפר הנוקדים" in workbook.title
    for page in workbook.pages:
        assert HEBREW.search(page.title), f"page {page.number} title is not Hebrew"
        assert HEBREW.search(page.instructions)


def test_image_prompts_stay_english(hebrew):
    """Image models are trained on English; the term map puts it back."""
    for page in hebrew.workbook.pages:
        assert not HEBREW.search(page.image_prompt), (
            f"page {page.number} prompt leaked Hebrew: {page.image_prompt[:120]}"
        )
        assert "Portrait A4" in page.image_prompt


def test_prompts_name_the_english_terms(hebrew):
    """The Hebrew landmark must arrive in the prompt as its English name."""
    maze = hebrew.workbook.page_by_type("maze")
    assert HEBREW.search(maze.instructions)
    joined = maze.image_prompt
    assert any(
        term in joined
        for term in ("the camel yard", "the Masada cliff fortress", "the date palm grove")
    )


def test_canonical_destination_stays_english(hebrew):
    """Slugs, filenames and the JSON field must not become Hebrew."""
    assert hebrew.workbook.destination == "Kfar Hanokdim"
    assert hebrew.bundle.context.slug == "kfar-hanokdim"
    for name in hebrew.bundle.prompts:
        assert not HEBREW.search(name)


def test_packing_reacts_to_hebrew_weather(hebrew):
    """Condition keywords are localized, so Hebrew weather text still matches."""
    packing = hebrew.workbook.page_by_type("packing")
    assert {"hot", "cold"} <= set(packing.metadata["matched_conditions"])
    assert "כובע שמש" in packing.metadata["items"]


def test_hebrew_word_search_uses_hebrew_letters(hebrew):
    page = hebrew.workbook.page_by_type("word_search")
    if page is None:
        pytest.skip("planner did not schedule a word search")
    assert HEBREW.search("".join(page.metadata["grid"]))
    for word in page.metadata["words"]:
        assert HEBREW.search(word)


def test_word_extraction_keeps_hebrew_but_folds_latin_accents():
    assert normalize("גמלים") == "גמלים"
    assert normalize("Český") == "CESKY"
    assert puzzle_word("עצי תמר") is not None


def test_rendered_page_is_marked_rtl(hebrew):
    markup = HtmlRenderer().render(hebrew.workbook, hebrew.bundle.context)
    assert 'dir="rtl"' in markup
    assert 'lang="he"' in markup
    assert "מאוזן" in markup or "תפזורת" in markup


def test_english_workbook_is_unaffected(builder):
    english = generate_workbook(
        destination="Kfar Hanokdim", children=["Noa"], ages=[7], write=False, builder=builder
    )
    assert not HEBREW.search(english.bundle.json)
    markup = HtmlRenderer().render(english.workbook, english.bundle.context)
    assert 'dir="ltr"' in markup
