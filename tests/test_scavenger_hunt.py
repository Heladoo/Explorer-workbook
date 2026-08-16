"""The scavenger hunt: a typeset table of separately drawn symbols.

The page deliberately does *not* ask one image prompt to draw a labelled grid,
because that is the shape image models get wrong. These tests pin the three
properties that replaced it: one prompt per picture, a table built by the
layout, and a sheet made mostly of things findable anywhere.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from src.activities._symbols import (
    UNIVERSAL_SYMBOLS,
    _topic,
    destination_symbols,
    grid_dimensions,
    hunt_size,
)
from src.activities.base import get_generator
from src.api import generate_workbook
from src.models.context import DestinationKnowledge, WorkbookContext
from src.models.plan import PlannedPage
from src.rendering.html_renderer import HtmlRenderer
from src.rendering.templates import esc
from src.strings import strings_for
from src.symbols import library

_HEBREW = re.compile(r"[֐-׿]")


def _draft(context, difficulty="medium", number=5):
    return get_generator("scavenger_hunt").generate(
        context,
        PlannedPage(number=number, activity_type="scavenger_hunt", difficulty=difficulty),
    )


# -- the symbol bank -----------------------------------------------------


def test_universal_symbols_have_unique_keys():
    keys = [symbol.key for symbol in UNIVERSAL_SYMBOLS]
    assert len(keys) == len(set(keys))


def test_every_universal_symbol_is_translated_in_every_locale():
    """A missing label silently degrades to English, so catch it here instead."""
    missing = {
        language: [
            symbol.key
            for symbol in UNIVERSAL_SYMBOLS
            if strings_for(language).optional(f"symbol.{symbol.key}", "") == ""
        ]
        for language in ("en", "he")
    }
    assert not any(missing.values()), missing


def test_every_library_symbol_is_translated_in_every_locale():
    """Wider than the pool above: a `draft`/`local` entry still needs a label
    the moment a future consumer (packing, a scored hunt) picks it — waiting
    until it joins the universal pool to translate it would be too late."""
    missing = {
        language: [
            symbol.key
            for symbol in library().all()
            if strings_for(language).optional(f"symbol.{symbol.key}", "") == ""
        ]
        for language in ("en", "he")
    }
    assert not any(missing.values()), missing


def test_destination_symbols_key_off_english_not_the_localized_label():
    """A Hebrew phrase slugifies to nothing, so the English term is what key
    derivation (and library lookup) must go through — never the localized
    label. Uses a phrase whose English term matches a real, ready library
    entry: a phrase with no library match at all mints a fresh symbol with
    no committed art, which is now dropped entirely rather than surfaced
    (see test_a_destination_symbol_with_no_cutout_is_dropped) — the property
    this test pins survives that fix; only the label a bare mint would have
    carried does not."""
    knowledge = DestinationKnowledge(
        wildlife=("הר",),
        illustration_terms=(("הר", "mountain"),),
        source="test",
    )
    context = WorkbookContext(destination="Kfar Hanokdim", knowledge=knowledge, language="he")
    symbols = destination_symbols(context)

    assert [symbol.key for symbol in symbols] == ["mountain"]


# -- short, general topics ------------------------------------------------


def test_landmarks_never_become_symbols():
    """A landmark is a place name by definition — excluded entirely, not
    just shortened."""
    knowledge = DestinationKnowledge(
        landmarks=("the Masada cliff fortress", "the Dead Sea shore"), source="test"
    )
    context = WorkbookContext(destination="Somewhere", knowledge=knowledge)
    assert destination_symbols(context) == ()


@pytest.mark.parametrize(
    "phrase,expected",
    [
        ("dolphins off the Pagasetic Gulf", "dolphins"),
        ("fresh pita from the saj", "fresh pita"),
        ("sweet tea with na'ana mint", "sweet tea"),
        ("desert wildflowers after rain", "desert wildflowers"),
        ("ducks by the riverbank", "ducks"),
        ("the date palm grove", "date palm grove"),
        ("goats grazing the hillsides", "goats grazing"),
        ("wild oregano and sage on the hillsides", "wild oregano"),
        ("Nubian ibex", "Nubian ibex"),
        ("camels", "camels"),
    ],
)
def test_destination_topics_are_short_and_general(phrase, expected):
    """The exact case from the brief: 'dolphins', never 'dolphins off the
    Pagasetic Gulf' — a knowledge phrase is prose, not a checklist word.

    Tests ``_topic()`` directly rather than round-tripping through
    ``destination_symbols()``: a topic that happens to match a committed
    library symbol (see the test below) legitimately gets *that* symbol's
    own label instead, which is a different concern from the shortening
    this test pins.
    """
    assert _topic(phrase) == expected


@pytest.mark.parametrize(
    "phrase,expected_key,expected_label",
    [
        # Exact key match, via slugify(_topic(phrase)).
        ("Nubian ibex on the ridge", "nubian-ibex", "a Nubian ibex"),
        # Exact key match, no aliasing needed.
        ("dolphins off the Pagasetic Gulf", "dolphins", "dolphins"),
        # Needs an alias: the natural topic ("goats grazing") doesn't slugify
        # onto the "goat" key.
        ("goats grazing the hillsides", "goat", "a goat"),
        ("owls in the old plane trees", "owl", "an owl"),
        ("wild tortoises in the forest", "turtle", "a tortoise"),
    ],
)
def test_a_destination_phrase_matching_the_library_reuses_its_symbol(
    phrase, expected_key, expected_label
):
    """A phrase whose topic resolves onto a `ready` library entry (by key or
    by alias) gets that entry's own artwork and label — not a fresh,
    artwork-less mint of the same thing under a slightly different key. This
    is what makes a destination's own wildlife/food facts actually
    illustrated instead of printing as a placeholder forever."""
    knowledge = DestinationKnowledge(wildlife=(phrase,), local_food=(phrase,), source="test")
    context = WorkbookContext(destination="Somewhere", knowledge=knowledge)
    symbols = destination_symbols(context)
    assert len(symbols) == 1, "wildlife and local_food resolved onto the same phrase twice"
    assert symbols[0].key == expected_key
    assert symbols[0].label == expected_label


def test_a_phrase_with_no_library_match_is_dropped_not_minted():
    """The old counterpart to the test above: a phrase with no library match
    at all — by key or by alias — used to still mint a fresh, artwork-less
    symbol ("fresh-pita" from "fresh pita from the saj"). It no longer does;
    see test_a_destination_symbol_with_no_cutout_is_dropped for why, and
    that the wildlife/local_food dedup this test used to also cover still
    holds (contributing nothing twice is as good as contributing nothing)."""
    phrase = "fresh pita from the saj"
    knowledge = DestinationKnowledge(wildlife=(phrase,), local_food=(phrase,), source="test")
    context = WorkbookContext(destination="Somewhere", knowledge=knowledge)
    assert destination_symbols(context) == ()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_local_symbol_label_is_at_most_three_words(context, difficulty):
    draft = _draft(context, difficulty)
    for symbol in draft.symbols:
        if not symbol.universal:
            assert len(symbol.label.split()) <= 3, symbol.label


def test_a_topic_never_ends_on_a_dangling_connector():
    """The word-count cap can itself land mid-phrase; the trailing word must
    always be a real content word, not an article or conjunction."""
    from src.activities._symbols import _TRAILING_STOPWORDS, _topic

    for phrase in (
        "goats grazing the hillsides",
        "wild oregano and sage on the hillsides",
        "spoon sweets made from local fruit",
    ):
        assert _topic(phrase).split()[-1].lower() not in _TRAILING_STOPWORDS


def test_destination_entries_with_no_english_form_are_dropped():
    """Rather than given an unstable or empty key."""
    knowledge = DestinationKnowledge(wildlife=("גמלים",), source="test")
    context = WorkbookContext(destination="Somewhere", knowledge=knowledge, language="he")
    assert destination_symbols(context) == ()


# -- artwork-less symbols never reach print --------------------------------


def test_a_destination_symbol_with_no_cutout_is_dropped():
    """A phrase that matches no library entry at all mints a fresh symbol with
    no committed artwork by construction — printing it anywhere would show a
    raw English slug instead of a picture. That is exactly the shipped bug
    ('spetzofai-sausage-stew', 'cobblestone-kalderimi-paths-flag' on a maze
    goal marker) — the fresh mint must be skipped, not surfaced."""
    knowledge = DestinationKnowledge(
        local_food=("the extremely rare zorbling fizzwhistle stew",), source="test"
    )
    context = WorkbookContext(destination="Nowhere", knowledge=knowledge)
    assert destination_symbols(context) == ()


def test_no_symbol_without_a_cutout_ever_reaches_a_hunt_page(context):
    """End to end, using the shared ``context`` fixture: its wildlife/plants/
    local_food phrases ("grey seals", "fish pie", ...) resolve onto no
    library entry, so before the fix in ``destination_symbols()`` they would
    mint artwork-less symbols and print in the grid as a raw English slug.
    Every symbol that actually reaches the page must have a real cutout on
    disk."""
    from src.symbol_art import CUTOUTS, find_variant

    for difficulty in ("easy", "medium", "hard"):
        draft = _draft(context, difficulty)
        # Universal-pool and library-matched symbols are already guaranteed
        # a cutout (see test_symbol_art.py) — only a destination-minted
        # symbol (no facets) is at risk, so that's what this isolates.
        local_keys = [s.key for s in draft.symbols if not s.universal]
        art = find_variant(local_keys, CUTOUTS)
        assert set(local_keys) <= set(art)


# -- Hebrew (and other non-English) topics never end mid-phrase ------------


@pytest.mark.parametrize(
    "phrase,expected",
    [
        # The two phrases the brief calls out by name, straight from
        # data/destinations/pelion.he.json: capping at 3 words used to land
        # squarely on a dangling proclitic in both cases — "מפירות" ("from
        # fruits") dropped the "local" it needed, and "בעצי" ("in the trees
        # of") is itself an unfinished construct-state noun with no object.
        ("צרצרים שרים בעצי הערמונים", "צרצרים שרים"),
        ("ריבת כפית מפירות מקומיים", "ריבת כפית"),
        # A third real phrase, included for its honest limitation rather
        # than hidden: "כפית" ("spoon") itself starts with כ, one of the
        # proclitic letters, so the guard drops it too even though it is a
        # real word here, not a "like/as" prefix. There is no way to tell
        # the two apart without real morphology — see
        # _ends_on_a_dangling_hebrew_prefix's docstring — so this is the
        # conservative, safe-but-not-maximal trade-off by design: shorter
        # than ideal, never wrong.
        ("אכילת ריבת כפית בכיכר כפר מוצלת", "אכילת ריבת"),
        ("זהוב וצונן בסתיו, עונת הערמונים", "זהוב וצונן"),
    ],
)
def test_a_hebrew_topic_never_ends_mid_word_or_mid_preposition(phrase, expected):
    """The English-only ``_CONNECTORS``/``_TRAILING_STOPWORDS`` logic used to
    cap a Hebrew phrase by bare word count with no idea that its own last
    word might be a preposition/conjunction glued to the next (now dropped)
    word. Real phrases from data/destinations/pelion.he.json, the exact
    source of the shipped bug."""
    assert _topic(phrase) == expected


# -- pack-role items never leak into the spot list --------------------------


def test_a_pack_only_destination_match_is_excluded_from_local_pool():
    """``destination_symbols()`` can resolve directly onto a library entry
    that is ``pack``-only (sunscreen, hiking shoes, ...) via an exact key
    match — before this, only the universal half of ``_choose()`` excluded
    pack-only symbols; ``local_pool`` did not."""
    from src.activities.scavenger_hunt import _spot_eligible
    from src.symbols import library

    sunscreen = library()["sunscreen"]
    assert not _spot_eligible(sunscreen)

    knowledge = DestinationKnowledge(wildlife=("sunscreen",), source="test")
    context = WorkbookContext(destination="Somewhere", knowledge=knowledge)
    symbols = destination_symbols(context)
    assert symbols and symbols[0].key == "sunscreen"
    assert not any(_spot_eligible(s) for s in symbols)


def test_no_pack_only_symbol_ever_reaches_a_hunt_page(context):
    lib = library()
    for difficulty in ("easy", "medium", "hard"):
        draft = _draft(context, difficulty)
        for key in draft.metadata["symbol_keys"]:
            if key not in lib:
                continue  # a destination-minted symbol carries no roles at all
            facets = lib[key].facets
            if facets is None:
                continue
            assert not ("pack" in facets.roles and "spot" not in facets.roles), key


# -- choosing the sheet --------------------------------------------------


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_the_sheet_is_always_full(context, difficulty):
    draft = _draft(context, difficulty)
    total, _ = hunt_size(difficulty)
    assert len(draft.symbols) == total


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_the_sheet_never_falls_below_a_four_by_four_grid(difficulty):
    """16 cells is the floor: small enough for a 4-year-old to finish, but
    still enough to fill an A4 page rather than leaving it half-empty."""
    total, _ = hunt_size(difficulty)
    assert total >= 16


def test_every_difficulty_uses_a_four_by_four_grid(context):
    """16 cells, always — a medium/hard sheet used to grow to 20 (4x5), a
    size the print layout was never actually verified against and did
    overflow onto the next page (see test_no_page_overflows_its_sheet)."""
    assert hunt_size("easy")[0] == 16
    assert hunt_size("medium")[0] == 16
    assert hunt_size("hard")[0] == 16


@pytest.mark.parametrize("count,expected", [(16, (4, 4)), (20, (4, 5)), (9, (4, 3))])
def test_grid_dimensions_are_always_four_columns_wide(count, expected):
    assert grid_dimensions(count) == expected


def test_an_easy_hunt_is_entirely_everyday_things(context):
    """The whole point: a 4-year-old's sheet must be finishable anywhere."""
    draft = _draft(context, "easy")
    assert all(symbol.universal for symbol in draft.symbols)


def test_a_harder_hunt_still_belongs_to_the_destination():
    """A hard hunt should surface some of the destination's own matched
    sights, not rely purely on the always-findable universal pool.

    Unlike before, "local" content is no longer identified by
    ``symbol.universal`` being false — a destination phrase that resolves
    onto a real library entry (by key or alias) is legitimately
    ``universal=True`` too (see ``Symbol.universal``'s docstring: it is a
    *localization* fact, not a geography one), and a phrase with no library
    match is now dropped rather than surfaced as an artwork-less
    ``universal=False`` mint (see
    ``test_a_destination_symbol_with_no_cutout_is_dropped``). So this checks
    overlap with ``destination_symbols()`` directly, using phrases known to
    resolve via alias onto real, ready library entries (goat, tortoise) — a
    destination whose knowledge matches nothing in the library legitimately
    gets an all-universal sheet instead (see
    ``test_a_destination_with_no_knowledge_still_gets_a_full_sheet``)."""
    knowledge = DestinationKnowledge(
        wildlife=("goats grazing the hillsides", "wild tortoises in the forest"),
        source="test",
    )
    ctx = WorkbookContext(destination="Somewhere", knowledge=knowledge)
    draft = _draft(ctx, "hard")

    destination_keys = {symbol.key for symbol in destination_symbols(ctx)}
    hunt_keys = set(draft.metadata["symbol_keys"])
    local = hunt_keys & destination_keys
    assert local, "a hard hunt should include some real sights from the trip"
    assert len(local) < len(draft.symbols), "but never only rare, hard-to-find ones"


def test_a_hunt_never_shows_more_than_three_animals():
    """The universal pool's animal topic is deep (16 of 45 entries) and
    destination wildlife leans the same way — an unlucky draw could
    otherwise fill most of a 16-cell sheet with animals. Checked at "hard"
    (the largest sheet, and the difficulty most likely to draw enough
    symbols to exceed the cap by chance) across a spread of page numbers,
    since context.sample's RNG key is derived from planned.number."""
    from src.symbols import library

    lib = library()
    knowledge = DestinationKnowledge(
        wildlife=("dolphins in the bay", "owls in the pines", "eagles overhead"),
        source="test",
    )
    ctx = WorkbookContext(destination="Somewhere", knowledge=knowledge)
    scavenger_hunt = get_generator("scavenger_hunt")
    for number in range(2, 20):
        draft = scavenger_hunt.generate(
            ctx, PlannedPage(number=number, activity_type="scavenger_hunt", difficulty="hard")
        )
        animals = sum(
            1
            for key in draft.metadata["symbol_keys"]
            if key in lib and lib[key].facets and lib[key].facets.topic == "animals"
        )
        assert animals <= 3, f"page {number}: {animals} animals, keys={draft.metadata['symbol_keys']}"


def test_capping_animals_prefers_to_trim_the_universal_pool_not_the_trip():
    """The regression this guards: a destination whose *entire* local
    wildlife pool is animals (a common case — wildlife almost always is)
    must not lose those sights just because the universal side of the sheet
    also happened to draw several animals. Only two local sights here, both
    animals and both comfortably under the cap, so the fix (trim
    universal-pool animals before ever touching a local one) must leave both
    in every single run — not just on average."""
    knowledge = DestinationKnowledge(
        wildlife=("goats grazing the hillsides", "wild tortoises in the forest"),
        source="test",
    )
    ctx = WorkbookContext(destination="Somewhere", knowledge=knowledge)
    destination_keys = {symbol.key for symbol in destination_symbols(ctx)}
    scavenger_hunt = get_generator("scavenger_hunt")

    for number in range(2, 20):
        draft = scavenger_hunt.generate(
            ctx, PlannedPage(number=number, activity_type="scavenger_hunt", difficulty="hard")
        )
        local = set(draft.metadata["symbol_keys"]) & destination_keys
        assert local, f"page {number}: lost every local sight to the animal cap"


def test_a_destination_with_no_knowledge_still_gets_a_full_sheet():
    """The universal pool tops up whatever the destination cannot supply."""
    bare = WorkbookContext(destination="Nowhere", knowledge=DestinationKnowledge(source="test"))
    draft = _draft(bare, "hard")
    total, _ = hunt_size("hard")

    assert len(draft.symbols) == total
    assert all(symbol.universal for symbol in draft.symbols)


def test_the_activity_supports_a_destination_it_knows_nothing_about():
    """Unlike most activities, this one needs no knowledge at all."""
    bare = WorkbookContext(destination="Nowhere", knowledge=DestinationKnowledge(source="test"))
    assert get_generator("scavenger_hunt").supports(bare)


def test_symbols_are_unique_within_a_sheet(context):
    draft = _draft(context, "hard")
    keys = [symbol.key for symbol in draft.symbols]
    assert len(keys) == len(set(keys))


def test_the_same_seed_picks_the_same_sheet(context):
    assert [s.key for s in _draft(context).symbols] == [s.key for s in _draft(context).symbols]


# -- one prompt per picture ----------------------------------------------


def test_symbols_get_no_per_book_prompt():
    """No specific symbol is minted per book any more (see src/pipeline.py) —
    the grid draws from the shared ``sources/symbols/`` cache, and new ones
    come from the doodle/grid sheet instead, not a one-off prompt per icon."""
    result = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    page = result.workbook.page_by_type("scavenger_hunt")

    assert page.symbols
    for symbol in page.symbols:
        assert symbol.prompt == ""
        assert symbol.prompt_filename not in result.bundle.prompts


def test_a_symbol_prompt_asks_for_one_object_and_no_furniture():
    """The grid, the boxes and the words are the layout's job, not the model's.

    ``render_symbol`` itself is unchanged and still exercised directly by the
    symbol-authoring tooling (``src/image_backends/sources.py``), just no
    longer called once per book.
    """
    from src.agents.prompt_generator import PromptGenerator
    from src.models.page import SymbolBrief

    symbol = UNIVERSAL_SYMBOLS[0]
    brief = SymbolBrief(key=symbol.key, label=symbol.label, subject=symbol.subject, universal=True)
    prompt = PromptGenerator().render_symbol(
        brief, WorkbookContext(destination="Kfar Hanokdim", knowledge=DestinationKnowledge(source="test"))
    )

    assert "A single centred object" in prompt
    for forbidden in ("checkbox", "border", "frame", "background"):
        assert f"no {forbidden}" in prompt
    assert "No text, letters, numbers" in prompt


def test_a_universal_symbol_prompt_never_mentions_the_destination():
    """This is what lets one drawing be cached and reused across every book."""
    kfar = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    prague = generate_workbook(destination="Prague", page_count=12, write=False)

    by_key = {
        symbol.key: symbol.prompt
        for result in (kfar, prague)
        for symbol in result.workbook.page_by_type("scavenger_hunt").symbols
        if symbol.universal
    }
    for key, prompt in by_key.items():
        assert "Kfar Hanokdim" not in prompt and "Prague" not in prompt, key


def test_the_same_universal_symbol_renders_identically_in_two_books():
    """A universal symbol's prompt depends only on its own subject and the
    book's age band, never on the destination — the property that lets
    ``sources/symbols/images/<key>.*`` be generated once and reused by every
    book that draws it.

    Checked directly against ``PromptGenerator`` rather than by generating two
    full books and hoping their independently-sampled hunts happen to share a
    key: with the pool now well past a couple of dozen entries and a hunt
    drawing well under half of it, two arbitrary destinations sharing no key
    at all is an ordinary, expected outcome, not a bug."""
    from src.agents.prompt_generator import PromptGenerator
    from src.models.page import SymbolBrief

    symbol = UNIVERSAL_SYMBOLS[0]
    brief = SymbolBrief(key=symbol.key, label=symbol.label, subject=symbol.subject, universal=True)
    generator = PromptGenerator()

    kfar = WorkbookContext(destination="Kfar Hanokdim", knowledge=DestinationKnowledge(source="test"))
    prague = WorkbookContext(destination="Prague", knowledge=DestinationKnowledge(source="test"))

    assert generator.render_symbol(brief, kfar) == generator.render_symbol(brief, prague)


def test_no_symbol_prompt_files_are_written(tmp_path):
    """``prompts/symbols/`` is no longer populated per book — new symbol
    artwork is sourced from the doodle/grid sheet instead (see
    ``prompts/doodle_grid.md`` and the symbol-authoring skill)."""
    result = generate_workbook(
        destination="Kfar Hanokdim", page_count=12, output_dir=tmp_path / "book"
    )
    symbols_dir = result.artifacts.output_dir / "prompts" / "symbols"
    assert not symbols_dir.exists() or not list(symbols_dir.glob("*.md"))


def test_the_page_carries_no_illustration_of_its_own():
    """The grid is typeset entirely from ``symbols`` — no page-level header
    illustration is requested any more."""
    result = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    page = result.workbook.page_by_type("scavenger_hunt")

    assert page.image_brief is None
    assert page.image_prompt == ""
    assert page.metadata["needs_illustration"] is False


# -- the printed table ---------------------------------------------------


def _grid(html: str) -> str:
    match = re.search(r'<ul class="spotting".*?</ul>', html, re.S)
    assert match, "the scavenger hunt page should print a spotting grid"
    return match.group(0)


def test_the_grid_prints_one_cell_per_symbol():
    result = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    page = result.workbook.page_by_type("scavenger_hunt")
    grid = _grid(HtmlRenderer().render(result.workbook, result.bundle.context))

    assert grid.count('class="spotting-cell"') == len(page.symbols)
    assert grid.count('class="checkbox"') == len(page.symbols)
    for symbol in page.symbols:
        assert esc(symbol.label) in grid


def test_the_grid_declares_its_own_dimensions_for_the_print_css():
    """The CSS sizes rows explicitly (grid-template-rows) rather than letting
    them grow with content, so a full sheet can never overflow the printed
    page — that only works if the columns/rows the layout emits actually
    match the symbol count."""
    result = generate_workbook(
        destination="Kfar Hanokdim", difficulty="hard", page_count=12, write=False
    )
    page = result.workbook.page_by_type("scavenger_hunt")
    grid = _grid(HtmlRenderer().render(result.workbook, result.bundle.context))

    columns, rows = grid_dimensions(len(page.symbols))
    assert f"--spotting-columns: {columns}" in grid
    assert f"--spotting-rows: {rows}" in grid
    assert columns * rows >= len(page.symbols)


def test_the_cell_box_is_white_with_a_grey_outline_not_the_theme_color():
    """Every other card in the book borrows the per-activity accent color for
    its outline; the spotting grid deliberately doesn't, so 20 cells of
    color don't turn the page into a wall of teal."""
    from src.rendering.templates import TemplateSet

    css = TemplateSet().read_asset("book.css")
    match = re.search(r"\.spotting-cell\s*\{([^}]*)\}", css, re.S)
    assert match, "no .spotting-cell rule found in book.css"
    rule = match.group(1)

    assert "background: var(--paper)" in rule
    assert "border-color: var(--line)" in rule
    assert "--accent" not in rule


def test_cells_without_artwork_name_the_symbol_they_are_waiting_for():
    result = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    page = result.workbook.page_by_type("scavenger_hunt")
    grid = _grid(HtmlRenderer().render(result.workbook, result.bundle.context))

    for symbol in page.symbols:
        assert f'<span class="spotting-ref">{symbol.key}</span>' in grid


def test_supplying_a_symbol_image_replaces_only_that_cell(tmp_path):
    result = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    page = result.workbook.page_by_type("scavenger_hunt")
    drawing = tmp_path / "one.png"
    drawing.write_bytes(b"png")

    grid = _grid(
        HtmlRenderer().render(
            result.workbook, result.bundle.context, symbol_images={page.symbols[0].key: drawing}
        )
    )

    assert grid.count('class="spotting-art filled"') == 1
    assert grid.count('<img ') == 1
    assert grid.count('class="spotting-ref"') == len(page.symbols) - 1


def test_the_grid_escapes_its_labels():
    """A knowledge pack with markup in it must not break the printed page."""
    nasty = "<script>alert(1)</script>"
    result = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    page = result.workbook.page_by_type("scavenger_hunt")
    poisoned = replace(
        page, symbols=tuple(replace(symbol, label=nasty) for symbol in page.symbols)
    )
    workbook = replace(result.workbook, pages=(poisoned,))

    html = HtmlRenderer().render(workbook, result.bundle.context)

    assert nasty not in html
    assert "&lt;script&gt;" in html


# -- localization --------------------------------------------------------


def test_a_hebrew_hunt_keeps_english_keys_and_english_prompts():
    """One drawing serves both books; only what the child reads is translated."""
    english = generate_workbook(destination="Kfar Hanokdim", page_count=12, write=False)
    hebrew = generate_workbook(
        destination="Kfar Hanokdim", language="he", page_count=12, write=False
    )
    en_page = english.workbook.page_by_type("scavenger_hunt")
    he_page = hebrew.workbook.page_by_type("scavenger_hunt")

    assert [s.key for s in en_page.symbols] == [s.key for s in he_page.symbols]
    for symbol in he_page.symbols:
        assert symbol.subject.isascii(), f"{symbol.key} subject must stay English"
        # The prompt template itself uses bullets and em-dashes, so test for
        # Hebrew specifically rather than for pure ASCII.
        assert not _HEBREW.search(symbol.prompt), f"{symbol.key} prompt must stay English"


def test_a_hebrew_hunt_translates_what_the_child_reads():
    hebrew = generate_workbook(
        destination="Kfar Hanokdim", language="he", page_count=12, write=False
    )
    page = hebrew.workbook.page_by_type("scavenger_hunt")
    universal = [symbol for symbol in page.symbols if symbol.universal]

    assert universal
    for symbol in universal:
        assert not symbol.label.isascii(), f"{symbol.key} label was left in English"
