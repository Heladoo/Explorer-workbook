"""Hebrew end to end: translated copy, RTL layout, English prompts."""

from __future__ import annotations

import re

import pytest

from src import generate_workbook
from src.activities._wordbank import normalize, puzzle_word
from src.activities.base import VISUAL_CATEGORIES
from src.agents.destination_agent import FileKnowledgeProvider
from src.qa import find_english_leaks
from src.rendering.html_renderer import HtmlRenderer
from src.strings import available_languages, strings_for

from tests.conftest import DATA_DIR

HEBREW = re.compile(r"[֐-׿]")
LATIN = re.compile(r"[A-Za-z]{2,}")


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
    """Without this the image prompt would carry Hebrew nouns.

    Goes through the provider rather than reading ``kfar-hanokdim.he.json``
    directly: the translation fragment only carries a ``translations`` map,
    not the category arrays themselves, so the thing worth pinning is the
    *resolved* knowledge — every Hebrew phrase the child sees has a matching
    English form to recover.
    """
    knowledge = FileKnowledgeProvider(DATA_DIR).fetch("Kfar Hanokdim", language="he")
    for category in ("landmarks", "wildlife", "plants", "activities", "local_food"):
        for phrase in knowledge.get(category):
            assert phrase in knowledge.english_terms, f"{phrase} has no English term for the prompt"
    assert not any(HEBREW.search(english) for english in knowledge.english_terms.values())


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
        if page.image_brief is None:
            continue
        assert not HEBREW.search(page.image_prompt), (
            f"page {page.number} prompt leaked Hebrew: {page.image_prompt[:120]}"
        )
        assert "Portrait A4" in page.image_prompt
    # The one prompt not tied to a page still carries the same contract.
    doodle_grid = hebrew.bundle.prompts["doodle_grid.md"]
    assert not HEBREW.search(doodle_grid), f"doodle grid prompt leaked Hebrew: {doodle_grid[:120]}"
    assert "Portrait A4" in doodle_grid


def test_prompts_name_the_english_terms(hebrew):
    """Every Hebrew knowledge term sampled onto the doodle/grid sheet must
    arrive in its prompt as the English name, not the Hebrew original."""
    context = hebrew.bundle.context
    doodle_grid = hebrew.bundle.prompts["doodle_grid.md"]
    subjects = [
        phrase
        for category in VISUAL_CATEGORIES
        for phrase in context.sample(context.knowledge.get(category), 4, key=f"doodle_grid:{category}")
    ]
    assert subjects, "fixture expects at least one visual knowledge entry"
    for phrase in subjects:
        assert context.knowledge.english_terms[phrase] in doodle_grid
        assert phrase not in doodle_grid


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
    assert "baseball-cap" in packing.metadata["pack_keys"]
    # The symbol keys stay English slugs (see qa.py's _SKIP_KEYS), but the
    # reader-facing labels the child would see (once the page has real
    # artwork's alt text, and in workbook.md) must be Hebrew like every other
    # page.
    for label in packing.metadata["items"] + packing.metadata["not_to_pack"]:
        assert not LATIN.search(label), f"{label!r} leaked English into a Hebrew page"
        assert HEBREW.search(label)


def test_hebrew_scavenger_hunt_items_have_no_latin_letters(hebrew):
    page = hebrew.workbook.page_by_type("scavenger_hunt")
    if page is None:
        pytest.skip("planner did not schedule a scavenger hunt")
    for item in page.metadata["items"]:
        assert not LATIN.search(item), f"{item!r} leaked English into a Hebrew page"
        assert HEBREW.search(item)


def test_qa_finds_no_english_leaks_with_a_translated_pack(hebrew):
    """Kfar Hanokdim has a full .he.json pack, so nothing should leak."""
    leaks = find_english_leaks(hebrew.workbook, hebrew.bundle.context)
    assert leaks == [], "\n".join(str(leak) for leak in leaks)


def test_qa_flags_english_facts_from_an_untranslated_pack(builder):
    """Without a translated pack, the destination's own facts stay English —
    the QA check should surface that, not silently hide it."""
    result = generate_workbook(
        destination="Prague",
        language="he",
        page_count=12,
        write=False,
        builder=builder,
    )
    leaks = find_english_leaks(result.workbook, result.bundle.context)
    assert leaks, "Prague has no prague.he.json — its English facts should be flagged"


def test_qa_ignores_the_destination_name_and_child_names(builder):
    result = generate_workbook(
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[7, 9],
        language="he",
        page_count=12,
        write=False,
        builder=builder,
    )
    for leak in find_english_leaks(result.workbook, result.bundle.context):
        assert "Noa" not in leak.words and "Amit" not in leak.words
        assert "Kfar" not in leak.words and "Hanokdim" not in leak.words


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
    # Kfar Hanokdim's own country (Israel) speaks Hebrew, so an English book
    # about it now deliberately carries ten real Hebrew words in the quiz
    # page's dictionary section (src/activities/quiz.py's phrasebook) — that
    # is the feature, not a leak. Excise just that field before checking
    # that nothing *else* in the book carries stray Hebrew.
    quiz = english.workbook.page_by_type("quiz")
    sanitized = quiz.metadata.get("dictionary", ())
    quiz.metadata["dictionary"] = ()
    try:
        assert not HEBREW.search(english.bundle.json)
    finally:
        quiz.metadata["dictionary"] = sanitized
    markup = HtmlRenderer().render(english.workbook, english.bundle.context)
    assert 'dir="ltr"' in markup


def test_qa_does_not_flag_a_deliberately_foreign_dictionary_word(builder):
    """A Prague/he book's quiz page carries ten real Czech words (the local
    language) — src/qa.py's _SKIP_KEYS must treat those, and the phrasebook
    bookkeeping around them, as by-design, not a leak.

    Prague has no curated Hebrew translation overlay, so its quiz page
    legitimately trips *other* findings here (an untranslated knowledge
    answer like "gingerbread hearts") — a real, pre-existing gap this test
    isn't about. Only ``metadata.dictionary`` findings are what's asserted.
    """
    prague_he = generate_workbook(
        destination="Prague", language="he", write=False, builder=builder
    )
    quiz = prague_he.workbook.page_by_type("quiz")
    entries = quiz.metadata["dictionary"]
    assert entries, "expected Prague/he to ship a Czech dictionary"

    findings = find_english_leaks(prague_he.workbook, prague_he.bundle.context)
    dictionary_findings = [f for f in findings if f.field == "metadata.dictionary"]
    assert not dictionary_findings, dictionary_findings


def test_qa_skips_a_latin_native_word_but_still_flags_a_latin_pronunciation():
    """``native`` is exempt from the scan even when it is genuinely Latin
    script (an English-speaking destination's phrasebook, e.g. Yellowstone,
    inside a Hebrew book) — deliberately foreign by design, like a symbol
    slug. ``pronunciation`` is not exempt: it must always be written in the
    workbook's own script, so a Latin transliteration inside a Hebrew book
    is a real bug and _SKIP_KEYS must keep catching it. One page carries
    both cases so a regression in either direction shows up here.
    """
    from src.models.page import Page
    from src.models.workbook import Workbook

    page = Page(
        number=1,
        type="quiz",
        title="החידון",
        instructions="הקיפו את התשובה",
        image_prompt="",
        metadata={
            "questions": [],
            "dictionary": [
                {
                    "concept": "thank_you",
                    "meaning": "תודה",
                    # Genuinely Latin script — Yellowstone's own language is
                    # English — and still must not be flagged.
                    "native": "Thank you",
                    # Wrong on purpose: an English transliteration where a
                    # Hebrew book must have a Hebrew one.
                    "pronunciation": "thank you",
                }
            ],
        },
    )
    workbook = Workbook(title="חוברת", destination="Yellowstone National Park", language="he", pages=(page,))
    findings = find_english_leaks(workbook)
    # _check_text reports a finding under its top-level metadata key
    # ("dictionary"), not a nested path, so the flagged *text* is what
    # distinguishes which field tripped it.
    assert any(f.text == "thank you" for f in findings), findings
    assert not any(f.text == "Thank you" for f in findings), findings
