"""The layout stage: HTML always, PDF when Playwright and Chromium are present."""

from __future__ import annotations

import html as html_module
import re

import pytest

from src import generate_workbook
from src.rendering.html_renderer import HtmlRenderer, _data_uri
from src.rendering.layouts import LAYOUTS
from src.rendering.templates import TemplateSet


@pytest.fixture
def rendered(builder):
    result = generate_workbook(
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[5, 7],
        write=False,
        builder=builder,
    )
    html = HtmlRenderer().render(result.workbook, result.bundle.context)
    return result, html


# -- document structure ------------------------------------------------


def test_every_page_becomes_a_printed_page(rendered):
    result, html = rendered
    for page in result.workbook.pages:
        assert f'id="page-{page.number}"' in html
    # One section per *rendered* page, plus the contents page. sheet_count,
    # not page_count: a centre spread is one section covering two of the
    # reader's page numbers.
    assert html.count('<section class="page') == result.workbook.sheet_count + 1


def test_the_document_is_print_styled_for_the_default_a5_booklet(rendered):
    _, html = rendered
    assert "size: A5 portrait" in html
    assert "page-break-after: always" in html
    assert "<style>" in html, "the CSS must be inlined so the file stands alone"


def test_the_a4_format_is_still_available_and_prints_at_a4(builder):
    """The original one-page-per-sheet format is a flag away, not gone."""
    result = generate_workbook(
        destination="Kfar Hanokdim", page_format="a4-portrait", write=False, builder=builder
    )
    html = HtmlRenderer(page_format="a4-portrait").render(
        result.workbook, result.bundle.context
    )
    assert "size: A4 portrait" in html
    assert "size: A5 portrait" not in html
    # No centre spread exists in a format that doesn't fold. Match the rule,
    # not the string: book.css's prose mentions "@page spread" by name.
    assert "@page spread {" not in html
    assert all(page.span == 1 for page in result.workbook.pages)


def test_html_carries_its_own_print_metadata(rendered):
    """<html> stamps the format/slot count it rendered with, so the
    in-browser editor's "Save as PDF" can print correctly even after the
    document has left this process — see src/rendering/print_metadata.py."""
    result, html = rendered
    assert 'data-page-format="a5-booklet"' in html
    assert f'data-page-count="{result.workbook.page_count}"' in html


def test_a4_html_carries_the_a4_format(builder):
    result = generate_workbook(
        destination="Kfar Hanokdim", page_format="a4-portrait", write=False, builder=builder
    )
    html = HtmlRenderer(page_format="a4-portrait").render(
        result.workbook, result.bundle.context
    )
    assert 'data-page-format="a4-portrait"' in html
    assert f'data-page-count="{result.workbook.page_count}"' in html


def test_contents_page_lists_every_page(rendered):
    result, html = rendered
    contents = html.split('<section class="page toc"')[1].split("</section>")[0]
    for page in result.workbook.pages:
        assert _esc(page.title) in contents


def test_contents_can_be_switched_off(rendered):
    result, _ = rendered
    html = HtmlRenderer(include_contents=False).render(
        result.workbook, result.bundle.context
    )
    assert "page toc" not in html


def test_instructions_and_titles_reach_the_page(rendered):
    result, html = rendered
    for page in result.workbook.pages:
        assert _esc(page.title) in html
        assert _esc(page.instructions) in html


def test_no_unsubstituted_placeholders(rendered):
    _, html = rendered
    assert not re.search(r"\$\{?[a-z_]+\}?", html), "a template placeholder leaked through"


def test_content_is_html_escaped(builder):
    """A destination or name with markup in it must not break the page."""
    result = generate_workbook(
        destination="Ampersand & <Angle> Bay",
        children=["<script>alert(1)</script>"],
        ages=[6],
        write=False,
        builder=builder,
    )
    html = HtmlRenderer().render(result.workbook, result.bundle.context)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "Ampersand &amp; " in html


# -- placeholders and real artwork ---------------------------------------


#: Types that still carry a page-level ``image_brief`` and so name their own
#: prompt file until real artwork replaces it — only cover and coloring pages
#: get one now (see src/pipeline.py). ``hidden_objects``/``spot_difference``
#: are paused (``enabled = False``) but still generatable, and unaffected by
#: that change. Every other type (drawing included) typesets its own working
#: area and carries no illustration of its own.
_PAGE_LEVEL_ART_TYPES = {
    "cover", "coloring", "hidden_objects",
    "spot_difference",
}


def test_pages_without_artwork_show_their_prompt_file(rendered):
    result, html = rendered
    for page in result.workbook.pages:
        if page.type in _PAGE_LEVEL_ART_TYPES:
            assert f"prompts/{page.prompt_filename}" in html
    assert "Illustration goes here" in html


def test_supplied_images_replace_the_placeholder(rendered, tmp_path):
    result, _ = rendered
    artwork = tmp_path / "cover.png"
    artwork.write_bytes(b"\x89PNG\r\n\x1a\n")

    html = HtmlRenderer().render(
        result.workbook, result.bundle.context, images={1: artwork}
    )
    assert "data:image/png;base64," in html
    assert 'class="art filled"' in html
    # Untouched pages keep their placeholder.
    assert "Illustration goes here" in html


# -- per-activity layouts -------------------------------------------------


def test_page_metadata_becomes_real_page_furniture(rendered):
    """The whole point of keeping text out of the illustration."""
    result, html = rendered

    packing = result.workbook.page_by_type("packing")
    packing_body = html.split(f'id="page-{packing.number}"')[1].split("</section>")[0]
    # No text/checkboxes on this page at all: the child connects a drawing
    # to the backpack, so nothing here should print an item's name. Strip the
    # placeholder's own debug reference (the symbol's *key*, shown only until
    # real artwork replaces it — this fixture renders no artwork at all) before
    # checking, since a key can coincide with its own label ("sunscreen").
    without_refs = re.sub(r'<span class="spotting-ref">[^<]*</span>', "", packing_body)
    for item in packing.metadata["items"] + packing.metadata["not_to_pack"]:
        assert _esc(item) not in without_refs
    ring_keys = packing.metadata["ring_keys"]
    total_nodes = len(ring_keys) + packing.metadata["blank_slots"]
    assert packing_body.count('class="packing-node"') == total_nodes
    assert packing_body.count("packing-item-blank") == packing.metadata["blank_slots"]

    # The quiz used to draw its options in picture boxes with the text
    # squeezed inside as a caption (see the module docstring history in
    # src/activities/quiz.py) — it is text-only now, so every option is a
    # lettered bubble, not an illustration frame.
    quiz = result.workbook.page_by_type("quiz")
    quiz_body = html.split(f'id="page-{quiz.number}"')[1].split("</section>")[0]
    for question in quiz.metadata["questions"]:
        assert _esc(question["question"]) in html
        for option in question["options"]:
            assert _esc(option) in html
    assert html.count('class="quiz-letter"') == sum(
        len(question["options"]) for question in quiz.metadata["questions"]
    )
    assert 'class="art"' not in quiz_body
    assert 'class="bubble"' not in quiz_body

    reflection = result.workbook.page_by_type("reflection")
    assert html.count('class="star outline"') >= reflection.metadata["stars"]
    for prompt in reflection.metadata["prompts"]:
        assert _esc(prompt) in html


def test_matching_prints_a_picture_per_pair_and_no_words(rendered):
    """The working area is two columns of pictures — a pre-reader must be able
    to do the page, so nothing inside it is labelled."""
    result, html = rendered
    matching = result.workbook.page_by_type("matching")
    body = html.split('id="page-%d"' % matching.number)[1].split("</section>")[0]
    left, right = body.split('class="matching-gutter"')

    pairs = matching.metadata["pair_count"]
    assert left.count('class="matching-cell"') == pairs
    assert right.count('class="matching-cell"') == pairs
    # One anchor per cell on each side, for the child to draw between.
    assert body.count('class="dot"') == 2 * pairs
    # Strip the placeholder's own debug reference (the symbol's *key*, shown
    # only until real artwork replaces it — this fixture renders no artwork
    # at all) before checking: a key can coincide with its own label
    # ("binoculars"), which isn't a real label leak.
    without_refs = re.sub(r'<span class="matching-ref">[^<]*</span>', "", body)
    for label in matching.metadata["left_column"]:
        assert _esc(label) not in without_refs


def test_matching_pairs_a_drawing_with_its_own_shadow(rendered):
    """Both columns are cut from one cached drawing per symbol, so the shadow
    is the same shape and size as its partner — and the columns disagree about
    the order, or the child could match straight across."""
    from src.symbol_art import artwork_for

    result, _ = rendered
    matching = result.workbook.page_by_type("matching")
    art = artwork_for(result.workbook)
    html = HtmlRenderer().render(
        result.workbook,
        result.bundle.context,
        symbol_cutouts=art.cutouts,
        symbol_shadows=art.silhouettes,
    )
    body = html.split('id="page-%d"' % matching.number)[1].split("</section>")[0]
    left, right = body.split('class="matching-gutter"')

    keys = matching.metadata["symbol_keys"]
    shadow_keys = matching.metadata["shadow_keys"]
    assert sorted(shadow_keys) == sorted(keys)
    assert shadow_keys != keys, "the shadow column must be reordered"

    for key in keys:
        assert _data_uri(art.cutouts[key]) in left
        assert _data_uri(art.silhouettes[key]) in right
    # The framed original never appears on this page: in the shadow column it
    # would be the answer, and in the drawing column it would be a ruled box.
    for key in keys:
        if key in art.images:
            assert _data_uri(art.images[key]) not in body


def test_spot_the_difference_gets_two_panels(builder):
    # spot_difference is paused (`enabled = False`) in the default catalogue,
    # so it's explicitly injected here to keep exercising its layout.
    from src.activities.base import get_generator
    from src.agents.planner import WorkbookPlanner
    from src.pipeline import WorkbookBuilder

    custom = WorkbookBuilder(
        knowledge_agent=builder.knowledge_agent,
        planner=WorkbookPlanner(
            [get_generator("cover"), get_generator("spot_difference"), get_generator("reflection")]
        ),
        clock=builder.clock,
    )
    result = generate_workbook(
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[5, 7],
        write=False,
        builder=custom,
    )
    html = HtmlRenderer().render(result.workbook, result.bundle.context)
    page = result.workbook.page_by_type("spot_difference")
    body = html.split('id="page-%d"' % page.number)[1].split("</section>")[0]
    assert body.count('class="art"') == 2


def test_an_activity_without_a_bespoke_layout_still_prints(rendered):
    """A new activity plugin must not need a layout to be printable."""
    result, html = rendered
    assert "coloring" not in LAYOUTS, "coloring deliberately uses the default full-page layout"
    coloring = result.workbook.page_by_type("coloring")
    body = html.split('id="page-%d"' % coloring.number)[1].split("</section>")[0]
    assert 'class="art"' in body
    assert _esc(coloring.title) in body


def test_the_maze_prints_as_an_svg(rendered):
    result, html = rendered
    maze = result.workbook.page_by_type("maze")
    body = html.split('id="page-%d"' % maze.number)[1].split("</section>")[0]
    grid = maze.metadata["grid"]
    assert f'viewBox="0 0 {grid["columns"]} {grid["rows"]}"' in body
    assert body.count('class="maze-endcap maze-endcap-') == 2


def test_page_sections_use_namespaced_classes(rendered):
    """A page class must not collide with an inner layout class.

    ``class="page matching"`` would let the ``.matching`` grid rule style the
    whole sheet, throwing the header and footer into the grid.
    """
    result, html = rendered
    from src.activities.base import ACTIVITY_REGISTRY

    for activity_type in ACTIVITY_REGISTRY:
        assert f'class="page {activity_type}"' not in html
    for page in result.workbook.pages:
        assert f'class="page page-{page.type}"' in html


def test_matching_shadows_are_not_in_the_same_order(rendered):
    """Otherwise every line is drawn straight across and the puzzle is free."""
    result, _ = rendered
    matching = result.workbook.page_by_type("matching")
    left = matching.metadata["left_column"]
    right = matching.metadata["right_column"]
    assert len(left) >= 3
    assert left != right
    assert sorted(left) == sorted(right)


def test_matching_always_has_five_or_six_pairs(rendered):
    """Fewer than five leaves the two columns looking sparse; past six the
    drawings print too small to tell apart by outline alone."""
    result, _ = rendered
    matching = result.workbook.page_by_type("matching")
    assert matching.metadata["pair_count"] in (5, 6)


def test_maze_start_marker_uses_the_borderless_cutout(rendered):
    """Both markers sit directly on the page background, not in a grid cell
    — a ruled square around either would look like a stray box."""
    from src.symbol_art import artwork_for

    result, _ = rendered
    art = artwork_for(result.workbook)
    assert "airplane" in art.cutouts, "fixture expects the airplane cut-out to exist"
    assert "airplane" in art.images, "fixture expects the framed original to exist too"
    html = HtmlRenderer().render(
        result.workbook,
        result.bundle.context,
        symbol_images=art.images,
        symbol_cutouts=art.cutouts,
    )
    maze = result.workbook.page_by_type("maze")
    body = html.split('id="page-%d"' % maze.number)[1].split("</section>")[0]
    start = body.split("maze-endcap-start")[1].split("maze-endcap-goal")[0]
    assert _data_uri(art.cutouts["airplane"]) in start
    assert _data_uri(art.images["airplane"]) not in start


def test_every_registered_layout_names_a_real_activity():
    from src.activities.base import ACTIVITY_REGISTRY

    assert set(LAYOUTS) <= set(ACTIVITY_REGISTRY)


def test_templates_report_a_missing_file_clearly():
    with pytest.raises(FileNotFoundError, match="missing template"):
        TemplateSet().get("body_nonexistent")


# -- writing ---------------------------------------------------------------


def test_hebrew_pelion_renders_rtl():
    """Pelion has no pelion.he.json — RTL layout and the TOC's localized
    headers must still hold up even when the destination pack itself stays
    English (see test_qa_flags_english_facts_from_an_untranslated_pack in
    test_localization.py for the companion QA-side check of that gap)."""
    result = generate_workbook(
        destination="Pelion",
        language="he",
        page_count=6,
        write=False,
    )
    html = HtmlRenderer().render(result.workbook, result.bundle.context)
    assert 'dir="rtl"' in html
    # The TOC header cells used to be hardcoded English literals in
    # toc.html.tmpl regardless of workbook language. The TOC no longer has
    # an ages column at all (ages aren't shown anywhere in the print layout).
    assert "<th>עמוד</th>" in html
    assert "<th>פעילות</th>" in html
    assert "Page</th>" not in html
    assert "Activity</th>" not in html
    assert "Ages</th>" not in html
    assert "גילאים" not in html


def test_embedded_fonts_are_self_contained(rendered):
    """The PDF is printed by whatever Chromium build happens to be on the
    machine running it, so every family must be embedded rather than named
    and hoped for — and Comic Sans must never come back."""
    _, html = rendered
    assert "@font-face" in html
    assert "font-family: 'Baloo 2'" in html
    assert "font-family: 'Nunito'" in html
    assert "font-family: 'Secular One'" in html
    assert "font-family: 'Assistant'" in html
    font_face_block = html.split("<style>")[1].split("</style>")[0]
    for line in font_face_block.splitlines():
        if "src:" in line:
            assert "url(data:font/woff2" in line, line
    assert "Comic Sans" not in html


def test_ink_saver_toggles_the_body_class(rendered):
    """book.css ships one static stylesheet with a `.ink-saver` override block
    that flattens every --brand-* token to grayscale; the flag only decides
    whether <body> carries that class, so the CSS text itself is identical
    either way — what must differ is the class, and the override rule must
    exist for it to do anything."""
    result, _ = rendered
    normal = HtmlRenderer(ink_saver=False).render(result.workbook, result.bundle.context)
    saved = HtmlRenderer(ink_saver=True).render(result.workbook, result.bundle.context)
    assert '<body class="">' in normal
    assert '<body class="ink-saver">' in saved
    assert "body.ink-saver" in normal and "body.ink-saver" in saved


def test_no_age_is_shown_anywhere(rendered):
    """Ages are dropped from the print layout entirely — the cover, page
    titles, the per-page chip and the table of contents never had a place
    for them to begin with, but this pins that no such placeholder exists to
    regress into."""
    _, html = rendered
    assert "age_label" not in html
    assert "&middot;" not in html  # the old chip's "TYPE · AGE" separator


def test_activity_groups_are_make_solve_look(rendered):
    """Only three activity groups exist — Make, Solve, Look — each a single
    CSS unit pairing --accent, --group-icon and --group-label so a page's
    color, icon and chip text always agree (see book.css)."""
    _, html = rendered
    css = html.split("<style>")[1].split("</style>")[0]
    for label in ('"Make"', '"Solve"', '"Look"'):
        assert f"--group-label: {label};" in css
    assert "--icon-make:" in css
    assert "--icon-solve:" in css
    assert "--icon-look:" in css
    # plan/reflect (packing, reflection, cover) were merged into Look rather
    # than kept as a fourth group. Found by direct substring search, not
    # regex: an unanchored `[^{}]*` before the literal makes `re.search` retry
    # from every position in this ~250KB stylesheet — quadratic, and ~22s in
    # practice for what should be a microsecond lookup.
    target = css.find(".page-cover")
    assert target != -1, "no rule block found for .page-cover"
    selector_start = css.rfind("}", 0, target) + 1
    brace_open = css.index("{", target)
    brace_close = css.index("}", brace_open)
    selector = css[selector_start:brace_open]
    body = css[brace_open + 1 : brace_close]
    assert ".page-scavenger_hunt" in selector
    assert ".page-packing" in selector
    assert ".page-reflection" in selector
    assert '--group-label: "Look"' in body


def test_page_chip_carries_an_icon_not_an_age(rendered):
    _, html = rendered
    assert 'class="chip-icon"' in html
    assert 'class="chip-label"' in html
    assert 'aria-hidden="true"' in html


def test_cover_logo_sits_above_the_art_on_a_white_page(rendered):
    """The Adventure Kit mark is a prominent top-of-cover mark now, not a
    small badge tucked in the name-line footer — it sits directly on the
    page body, which carries no background of its own and so stays --paper
    (the mark is only ever placed on white, never a color or tint)."""
    result, html = rendered
    cover = result.workbook.page_by_type("cover")
    body = html.split('id="page-%d"' % cover.number)[1].split("</section>")[0]
    logo_at = body.find('class="brand-logo')
    art_at = body.find('class="art')
    assert -1 < logo_at < art_at, "logo must come before the illustration, not inside the footer"
    assert '<div class="cover-footer">' in body
    assert logo_at < body.find('class="cover-footer"')

    css = html.split("<style>")[1].split("</style>")[0]
    assert "background" not in (css.split(".page {")[1].split("}")[0])


def test_the_name_area_has_a_visible_background(rendered):
    """Before this, .cover-footer was --paper (page white) with only a
    border for color — on a white page that read as a stray line, not a
    distinct writing area."""
    _, html = rendered
    css = html.split("<style>")[1].split("</style>")[0]
    match = re.search(r"\.cover-footer\s*\{([^}]*)\}", css)
    assert match, "no .cover-footer rule found"
    assert "background: var(--accent-tint)" in match.group(1)


def test_the_name_line_is_large_enough_to_actually_write_on(rendered):
    """The cover's name line is the book's one ownership moment for a young
    child — it used to give almost no writing height: --size-md text on a
    2px rule inside --space-4 padding. This pins the enlargement: bigger
    label text, a taller writing box above the rule, and more room around
    both."""
    _, html = rendered
    css = html.split("<style>")[1].split("</style>")[0]

    footer = re.search(r"\.cover-footer\s*\{([^}]*)\}", css)
    assert footer and "--space-6" in footer.group(1)

    name_line = re.search(r"\.name-line\s*\{([^}]*)\}", css, re.S)
    assert name_line and "font-size: var(--size-lg)" in name_line.group(1)

    rule = re.search(r"\.name-line \.rule\s*\{([^}]*)\}", css, re.S)
    assert rule, "no .name-line .rule rule found"
    assert "height: var(--space-6)" in rule.group(1)


def test_dict_pron_is_enlarged_but_keeps_its_italic_and_soft_color():
    """The pronunciation column used to inherit .dict-row > span's --size-sm
    (9.5pt) — the smallest, greyest text in the row, despite being the only
    column a Hebrew-reading child can actually sound out. Matched to
    .dict-native's own size; italic and the soft ink color are unchanged on
    purpose (explicitly requested to stay)."""
    css = TemplateSet().read_asset("book.css")
    match = re.search(r"\.dict-pron\s*\{([^}]*)\}", css, re.S)
    assert match, "no .dict-pron rule found in book.css"
    rule = match.group(1)
    assert "font-size: var(--size-md)" in rule
    assert "font-style: italic" in rule
    assert "color: var(--ink-soft)" in rule


def test_html_is_written_alongside_the_other_artifacts(tmp_path, builder):
    result = generate_workbook(
        destination="Prague",
        children=["Noa"],
        ages=[7],
        page_count=6,
        output_dir=tmp_path / "book",
        html=True,
        builder=builder,
    )
    artifacts = result.artifacts
    assert artifacts.workbook_html.exists()
    assert artifacts.workbook_pdf is None
    assert artifacts.workbook_html in artifacts.as_list()
    assert "Prague" in artifacts.workbook_html.read_text(encoding="utf-8")


# -- PDF -------------------------------------------------------------------


def _chromium_available() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    from src.rendering.pdf_renderer import find_chromium

    return find_chromium() is not None


requires_chromium = pytest.mark.skipif(
    not _chromium_available(), reason="Playwright with a Chromium build is not available"
)


@requires_chromium
@pytest.mark.parametrize(
    "destination,language",
    [
        ("Kfar Hanokdim", "en"),  # Hebrew dictionary word inside an LTR book
        ("Pelion", "he"),
        ("Pelion", "en"),  # Greek dictionary word inside an LTR book
        ("Prague", "he"),  # Latin/latin-ext dictionary word inside an RTL book
    ],
)
def test_no_page_overflows_its_sheet(destination, language, builder):
    """A page's own content must fit inside its fixed-height ``.page`` box.

    Content that doesn't — the scavenger hunt did, back when a "hard" sheet
    was 20 cells (4x5) instead of the current fixed 16 (4x4); see
    _symbols.py, and again on a real Pelion/he "hard" book where a
    flex:1 1 auto + min-height:0 area (the norm for every fixed-size working
    area on this page — the scavenger hunt grid, the matching columns) filled
    its box down to a measured 0.25px of slack, which live layout renders
    fine but print rasterization rounds independently and can tip over —
    has nowhere to go but visually past the bottom of its sheet, overlaying
    whatever prints on the next page.

    This is why ``.page`` carries an explicit ``overflow: hidden`` (see
    book.css): without it, ``.page`` never becomes a scroll container, so
    ``scrollHeight`` silently equals ``clientHeight`` *regardless of real
    overflow* — this test would report "fits" even while genuinely bleeding
    onto the next printed page, which is exactly how the Pelion/he case above
    slipped through here once already. With it, a real layout measurement in
    headless Chromium actually catches it, not a guess from the HTML source.
    ``.page`` also reserves 2mm nothing here ever uses, specifically so a
    flex-filled area's razor-thin, by-design-zero slack doesn't round the
    wrong way under print rasterization the way it did there.

    difficulty="hard" forces every difficulty-sized activity (scavenger
    hunt, word search, hidden objects, quiz, matching, ...) to render at
    its largest, most overflow-prone size in one pass.

    Real symbol artwork is passed in, not left as placeholders — a
    placeholder cell is a few lines of small reference text, a real cell is
    a full drawing, and only the latter is what --generate-images actually
    ships. A test that never renders a real <img> can't see whatever height
    difference that swap introduces.

    A self-contained ``with sync_playwright()`` per test, same as every
    other PDF test in this module — a shared browser fixture held open
    across tests collided with those other tests' own ``sync_playwright()``
    calls ("using Playwright Sync API inside the asyncio loop").

    No ``emulate_media("print")``: that disables book.css's ``@media
    screen`` block, which is the *only* place ``.page`` gets an explicit
    width — under print emulation ``.page`` falls back to 100% of the
    browser's default viewport (~1280px), far wider than any real page
    (A5's 148mm is ~559px), so far less text wraps and this test was
    measuring overflow at a width the book never actually prints at. The
    height constraint (``.page``'s ``height: calc(...)`` in the base rules)
    is not screen-scoped, so it was correct even under print emulation —
    only the width was silently wrong, which is exactly the dimension that
    decides how much a quiz option or a dictionary word wraps. Screen media
    is what the on-screen page preview exists for: it pins ``.page`` to
    ``var(--page-width)``/``var(--page-height)``, the same values the real
    ``@page`` rule prints at, so this now reflows content at the width the
    book actually ships with.
    """
    from playwright.sync_api import sync_playwright
    from src.image_backends.sources import DEFAULT_SOURCES_DIR
    from src.rendering.pdf_renderer import find_chromium

    result = generate_workbook(
        destination=destination,
        language=language,
        difficulty="hard",
        write=False,
        builder=builder,
    )
    symbol_images = {
        path.stem: path for path in (DEFAULT_SOURCES_DIR / "images").glob("*.png")
    }
    # Cut-outs and silhouettes too, not just the framed "images" sheet: the
    # scavenger hunt grid renders cut-outs (see layouts.py's _spotting_grid)
    # and the matching page renders both derived variants — a run that never
    # passes them never exercises the code path that actually ships.
    symbol_cutouts = {
        path.stem: path for path in (DEFAULT_SOURCES_DIR / "cutouts").glob("*.png")
    }
    symbol_shadows = {
        path.stem: path for path in (DEFAULT_SOURCES_DIR / "silhouettes").glob("*.png")
    }
    html = HtmlRenderer().render(
        result.workbook,
        result.bundle.context,
        symbol_images=symbol_images,
        symbol_cutouts=symbol_cutouts,
        symbol_shadows=symbol_shadows,
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=find_chromium())
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            overflowing = page.eval_on_selector_all(
                "section.page",
                "els => els.map(el => [el.id, el.scrollHeight - el.clientHeight])"
                ".filter(([, over]) => over > 1)",  # >1px of slack for subpixel rounding
            )
        finally:
            browser.close()

    assert not overflowing, (
        f"{destination}/{language}: pages overflow their own sheet by more "
        f"than 1px (id, overflow_px): {overflowing}"
    )


@requires_chromium
def test_no_native_word_falls_back_to_a_system_font(builder):
    """The dictionary's native-word column must render from *our* embedded
    Noto Sans face, not whatever Greek-capable font the printing machine
    happens to have installed — the entire point of src/fonts.py's
    on-demand embedding.

    Two measurement approaches turn out not to work, both discovered by
    running this test against a deliberately broken render (no Greek face
    embedded at all) as a negative control before trusting the real one:

    - ``getBoundingClientRect().width`` / ``scrollWidth`` on ``.dict-native``
      itself: it is a CSS Grid item in a ``1fr`` column, so both are the
      grid track's box size, not the text's — identical regardless of font.
    - Comparing the real render's width against a *nonexistent* sentinel
      font-family: this machine (like most) already has *some* Greek-capable
      system font, so "our embedded face" and "system fallback" are both
      real, non-identical-but-nonzero widths compared to the sentinel —
      the comparison can't tell them apart and reports "fine" either way.

    What actually works: measure the glyph run's own extent with a DOM
    ``Range`` (unaffected by the grid item's box size), once with the real
    stack and once with *only "Noto Sans" removed* from it (leaving Nunito,
    Segoe UI, sans-serif — the same fallback chain minus our embedded face).
    If removing it changes nothing, Noto Sans was never the one drawing this
    glyph to begin with.
    """
    from playwright.sync_api import sync_playwright
    from src.rendering.pdf_renderer import find_chromium

    result = generate_workbook(
        destination="Pelion", language="he", difficulty="hard", write=False, builder=builder
    )
    html = HtmlRenderer().render(result.workbook, result.bundle.context)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=find_chromium())
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="load")
            page.evaluate("document.fonts.ready")
            measurements = page.eval_on_selector_all(
                ".dict-native",
                """els => els.map(el => {
                    const textNode = el.firstChild;
                    const range = document.createRange();
                    range.selectNodeContents(textNode);
                    const withNotoSans = range.getBoundingClientRect().width;
                    const original = el.style.fontFamily;
                    el.style.fontFamily = "Nunito, 'Segoe UI', sans-serif";
                    const withoutNotoSans = range.getBoundingClientRect().width;
                    el.style.fontFamily = original;
                    return [el.textContent, withNotoSans, withoutNotoSans];
                })""",
            )
        finally:
            browser.close()

    assert measurements, "expected at least one .dict-native cell (Pelion/he ships a Greek dictionary)"
    for text, with_noto, without_noto in measurements:
        assert with_noto != without_noto, (
            f"{text!r} rendered at the same width with 'Noto Sans' removed from the font "
            "stack — our embedded face isn't the one drawing this glyph, so it fell back to "
            "the printing machine's own font (or Nunito silently gained Greek coverage)."
        )


@requires_chromium
def test_pdf_is_produced_and_is_a_valid_a4_document(tmp_path, builder):
    result = generate_workbook(
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[5, 7],
        page_count=6,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    pdf = result.artifacts.workbook_pdf

    assert pdf.exists()
    raw = pdf.read_bytes()
    assert raw.startswith(b"%PDF-")
    assert raw.rstrip().endswith(b"%%EOF")
    # One page per activity — the PDF prints without a table of contents.
    assert raw.count(b"/Type /Page\n") == result.workbook.page_count
    assert result.artifacts.workbook_html.exists(), "--pdf keeps the HTML it printed"


@requires_chromium
def test_pelion_hebrew_pdf_is_a_valid_a4_document(tmp_path, builder):
    """RTL layout, embedded Hebrew type and the redesigned page furniture all
    have to survive an actual print pass, not just render as HTML."""
    result = generate_workbook(
        destination="Pelion",
        language="he",
        page_count=6,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    pdf = result.artifacts.workbook_pdf

    assert pdf.exists()
    raw = pdf.read_bytes()
    assert raw.startswith(b"%PDF-")
    assert raw.rstrip().endswith(b"%%EOF")
    assert raw.count(b"/Type /Page\n") == result.workbook.page_count
    assert result.artifacts.workbook_html.exists(), "--pdf keeps the HTML it printed"
    assert 'dir="rtl"' in result.artifacts.workbook_html.read_text(encoding="utf-8")


@requires_chromium
def test_pdf_can_be_produced_without_leaving_html_behind(tmp_path, builder):
    from src.rendering.pdf_renderer import PdfRenderer

    result = generate_workbook(
        destination="Prague", page_count=4, write=False, builder=builder
    )
    target = tmp_path / "quiet" / "book.pdf"
    PdfRenderer(keep_html=False).render(
        result.workbook, result.bundle.context, output_path=target
    )
    assert target.exists()
    assert not target.with_suffix(".html").exists()


@requires_chromium
def test_render_html_prints_an_already_rendered_document(tmp_path, builder):
    """The in-browser editor's "Save as PDF" has finished markup, not a
    Workbook — ``render_html`` must print that directly, byte-for-byte the
    same document, and produce the same page count as ``render`` would from
    the Workbook it came from."""
    from src.rendering.pdf_renderer import PdfRenderer

    result = generate_workbook(
        destination="Prague", page_count=4, write=False, builder=builder
    )
    html = HtmlRenderer(include_contents=False).render(
        result.workbook, result.bundle.context
    )
    target = tmp_path / "edited.pdf"
    PdfRenderer(keep_html=False).render_html(html, target)

    assert target.exists()
    raw = target.read_bytes()
    assert raw.startswith(b"%PDF-")
    assert raw.count(b"/Type /Page\n") == result.workbook.page_count


def _esc(value: str) -> str:
    """Templates escape everything they substitute, so assertions must too."""
    return html_module.escape(value, quote=True)
