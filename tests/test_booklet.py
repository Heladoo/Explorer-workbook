"""The A5 booklet: page format, the centre spread, and sheet imposition.

Everything here is about the book as a *physical object* — what folds, what
lands on which side of which sheet, and which edge the staple goes through.
"""

from __future__ import annotations

import pytest

from src import generate_workbook
from src.rendering.formats import FORMATS, PAGE_COUNT_CHOICES, get_format
from src.rendering.html_renderer import HtmlRenderer
from src.rendering.imposition import plan_booklet

#: An itinerary long enough for the route map to have a route to draw, which
#: is what makes it eligible for the centre spread at all (see map.py).
ITINERARY = ["Volos", "Makrinitsa", "Milies", "Tsagarada"]


def _booklet(builder, page_count=12, language="en", page_format="a5-booklet"):
    return generate_workbook(
        destination="Pelion",
        language=language,
        itinerary=ITINERARY,
        page_count=page_count,
        page_format=page_format,
        write=False,
        builder=builder,
    ).workbook


# -- page lengths --------------------------------------------------------


def test_every_offered_page_length_can_actually_fold():
    """The whole menu exists to guarantee this, so assert it directly rather
    than trusting that 8, 12 and 16 were chosen carefully."""
    for count in PAGE_COUNT_CHOICES:
        assert count % 4 == 0, f"{count} pages cannot be saddle-stitched"
        plan_booklet(count)  # raises if it can't


def test_a_length_that_cannot_fold_is_refused_rather_than_rounded():
    with pytest.raises(ValueError, match="multiple of 4"):
        plan_booklet(10)


# -- imposition ----------------------------------------------------------


@pytest.mark.parametrize("count", PAGE_COUNT_CHOICES)
def test_every_page_lands_on_exactly_one_sheet_side(count):
    plan = plan_booklet(count)
    placed = [number for side in plan.sides for number in side]
    assert sorted(placed) == list(range(1, count + 1))
    assert plan.sheet_count == count // 4


def test_the_outermost_sheet_carries_the_cover_and_the_back():
    """Fold a stack of sheets and the outside one becomes the cover: page 1
    on its right half and the last page on its left."""
    plan = plan_booklet(12)
    assert plan.sides[0] == (12, 1)


def test_the_innermost_sheet_side_is_the_centre_pair():
    """The reason a double-page spread can only live at the centre: those two
    pages are the only pair that shares one side of one sheet."""
    for count in PAGE_COUNT_CHOICES:
        plan = plan_booklet(count)
        assert plan.sides[-1] == (count // 2, count // 2 + 1)


def test_a_right_bound_book_mirrors_every_pair():
    """Hebrew opens from the right, so page 1 is the left-hand page of the
    first spread. Sheet order and fold are unchanged; only the pairs flip."""
    ltr = plan_booklet(12, binding="left")
    rtl = plan_booklet(12, binding="right")
    assert len(ltr.sides) == len(rtl.sides)
    for left_side, right_side in zip(ltr.sides, rtl.sides):
        assert right_side == left_side[::-1]


# -- the centre spread ---------------------------------------------------


@pytest.mark.parametrize("count", PAGE_COUNT_CHOICES)
def test_the_route_map_takes_the_exact_centre_of_the_booklet(builder, count):
    workbook = _booklet(builder, page_count=count)
    spreads = [page for page in workbook.pages if page.is_spread]

    assert len(spreads) == 1, "exactly one page may span the centre"
    spread = spreads[0]
    assert spread.type == "map"
    # The centre pair, and the pair the innermost sheet side actually carries.
    assert (spread.number, spread.number + 1) == (count // 2, count // 2 + 1)
    assert plan_booklet(count).sides[-1] == (spread.number, spread.number + 1)


def test_a_spread_costs_two_page_numbers_and_one_printed_page(builder):
    workbook = _booklet(builder, page_count=12)

    assert workbook.page_count == 12, "the reader still counts twelve pages"
    assert workbook.sheet_count == 11, "but only eleven get printed"
    # Page numbers still run 1..12 with nothing skipped and nothing repeated.
    covered = [n for page in workbook.pages for n in range(page.number, page.number + page.span)]
    assert covered == list(range(1, 13))


def test_the_spread_page_prints_as_one_landscape_area(builder):
    workbook = _booklet(builder, page_count=12)
    html = HtmlRenderer().render(
        workbook, _context(builder, page_count=12)
    )
    assert "@page spread" in html
    assert "page-spread" in html
    # Two facing pages, so the chip prints both numbers rather than making the
    # book look like it skips one.
    assert ">6-7<" in html


def test_the_spread_tells_its_image_prompt_that_it_is_landscape(builder):
    """A prompt with no aspect guidance produces a squarish image, which
    letterboxes into a 2:1 spread and wastes the width the spread is for."""
    workbook = _booklet(builder, page_count=12)
    spread = next(page for page in workbook.pages if page.is_spread)

    assert "landscape" in spread.image_prompt.lower()
    assert "fold" in spread.image_prompt.lower(), "the prompt must keep labels off the fold"


def test_without_an_itinerary_there_is_simply_no_spread(builder):
    """The map needs a real route to draw. No route, no map, no spread — and
    the book is still a valid, foldable 12 pages."""
    workbook = generate_workbook(
        destination="Kfar Hanokdim", page_count=12, write=False, builder=builder
    ).workbook

    assert all(page.span == 1 for page in workbook.pages)
    assert workbook.page_count == 12
    assert workbook.sheet_count == 12


def test_the_a4_format_has_no_centre_to_spread_across(builder):
    """A4 prints one page per sheet, so nothing folds and no page pair shares
    a sheet side. The map competes for an ordinary body slot instead."""
    workbook = _booklet(builder, page_count=12, page_format="a4-portrait")

    assert all(page.span == 1 for page in workbook.pages)
    assert "map" in workbook.activity_types, "the map is still a page, just not a spread"


def test_a_length_with_no_centre_falls_back_to_ordinary_pages(builder):
    """page_count // 2 is only a sheet boundary when the count is a multiple
    of 4. The planner still has to produce a coherent book when it isn't."""
    workbook = _booklet(builder, page_count=10)

    assert all(page.span == 1 for page in workbook.pages)
    assert workbook.page_count == 10


# -- binding side --------------------------------------------------------


def test_a_hebrew_book_moves_its_gutter_to_the_other_side(builder):
    """@page :left/:right mean the even/odd sheets of the print run and
    Chromium assigns them from page order alone. Which one carries the gutter
    depends on the binding edge, and Hebrew binds on the right."""
    workbook = _booklet(builder, page_count=12, language="he")
    html = HtmlRenderer().render(workbook, _context(builder, page_count=12, language="he"))

    fmt = get_format("a5-booklet")
    outer, inner = f"{fmt.margin_outer_mm:g}mm", f"{fmt.margin_inner_mm:g}mm"
    # The last rule wins, so the RTL override must come after the stylesheet's
    # own left-bound pair — assert on position, not just presence.
    override = html.rindex("@page :right")
    assert html.index(f"@page :right {{ margin-left: {outer}; margin-right: {inner}; }}") == override


def test_an_english_book_keeps_the_stylesheet_binding(builder):
    workbook = _booklet(builder, page_count=12)
    html = HtmlRenderer().render(workbook, _context(builder, page_count=12))
    assert "Right-bound (RTL) book" not in html


# -- format definitions --------------------------------------------------


@pytest.mark.parametrize("key", sorted(FORMATS))
def test_each_format_declares_the_page_size_its_stylesheet_prints(key):
    """formats.py and the stylesheet each state the page size, and only one
    of them is what actually reaches the printer. They must agree."""
    fmt = get_format(key)
    css = HtmlRenderer(page_format=fmt).templates.read_asset(fmt.css_filename)

    assert f"--page-width: {fmt.page_width_mm:g}mm" in css
    assert f"--page-height: {fmt.page_height_mm:g}mm" in css
    assert f"--page-margin-outer: {fmt.margin_outer_mm:g}mm" in css
    assert f"--page-margin-inner: {fmt.margin_inner_mm:g}mm" in css


def test_only_a_folding_format_is_imposed_onto_sheets():
    assert get_format("a5-booklet").booklet
    assert get_format("a5-booklet").sheet_width_mm == 297.0
    assert not get_format("a4-portrait").booklet
    assert get_format("a4-portrait").sheet_width_mm is None


def test_an_unknown_format_is_refused_by_name():
    with pytest.raises(ValueError, match="unknown page format"):
        get_format("a3-poster")


# -- the printed article -------------------------------------------------

from tests.test_rendering import requires_chromium  # noqa: E402

_MM = 72.0 / 25.4


def _sizes(path):
    from pypdf import PdfReader

    return [
        (float(page.mediabox.width) / _MM, float(page.mediabox.height) / _MM)
        for page in PdfReader(str(path)).pages
    ]


@requires_chromium
def test_the_pdf_really_prints_at_a5_with_one_landscape_spread(tmp_path, builder):
    """The single assumption the whole centre-spread design rests on: that a
    named ``@page`` keeps its own size inside one document. If a future engine
    stops honouring it, every spread silently prints at A5 with a layout built
    for twice the width — so this measures the finished PDF rather than
    trusting the CSS.
    """
    result = generate_workbook(
        destination="Pelion",
        itinerary=ITINERARY,
        page_count=12,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    sizes = _sizes(result.artifacts.workbook_pdf)

    assert len(sizes) == result.workbook.sheet_count == 11
    landscape = [i for i, (w, h) in enumerate(sizes, start=1) if w > h]
    assert len(landscape) == 1, f"expected exactly one spread, got sizes {sizes}"

    width, height = sizes[landscape[0] - 1]
    assert width == pytest.approx(297, abs=1.5), "the spread must be a full A4 landscape"
    assert height == pytest.approx(210, abs=1.5)
    for i, (w, h) in enumerate(sizes, start=1):
        if i != landscape[0]:
            assert (w, h) == pytest.approx((148, 210), abs=1.5), f"page {i} is not A5"


@requires_chromium
def test_the_booklet_pdf_is_foldable_a4_sheets_in_print_order(tmp_path, builder):
    result = generate_workbook(
        destination="Pelion",
        itinerary=ITINERARY,
        page_count=12,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    booklet = result.artifacts.workbook_booklet_pdf

    assert booklet is not None and booklet.exists()
    assert booklet in result.artifacts.as_list()
    sizes = _sizes(booklet)
    # Three sheets, two printed sides each — duplex.
    assert len(sizes) == 6
    for width, height in sizes:
        assert (width, height) == pytest.approx((297, 210), abs=0.5)


@requires_chromium
def test_the_page_pdf_survives_imposition_untouched(tmp_path, builder):
    """Two files, two jobs: workbook.pdf stays the readable book in reading
    order, and the imposed sheets are written alongside it, never instead."""
    result = generate_workbook(
        destination="Pelion",
        itinerary=ITINERARY,
        page_count=8,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    assert result.artifacts.workbook_pdf.exists()
    assert result.artifacts.workbook_booklet_pdf.exists()
    assert len(_sizes(result.artifacts.workbook_pdf)) == result.workbook.sheet_count
    assert len(_sizes(result.artifacts.workbook_booklet_pdf)) == 4


@requires_chromium
def test_no_sheets_are_written_for_a_format_that_does_not_fold(tmp_path, builder):
    result = generate_workbook(
        destination="Pelion",
        itinerary=ITINERARY,
        page_count=12,
        page_format="a4-portrait",
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    assert result.artifacts.workbook_pdf.exists()
    assert result.artifacts.workbook_booklet_pdf is None


@requires_chromium
def test_a_length_that_cannot_fold_costs_the_sheets_not_the_book(tmp_path, builder, caplog):
    """A book is already fully rendered by the time imposition runs, so an
    unfoldable length must lose the second file and say so — not the run."""
    result = generate_workbook(
        destination="Pelion",
        itinerary=ITINERARY,
        page_count=10,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    assert result.artifacts.workbook_pdf.exists(), "the readable book is unaffected"
    assert result.artifacts.workbook_booklet_pdf is None
    assert any("not a multiple of 4" in record.message for record in caplog.records)


@requires_chromium
def test_the_centre_spread_prints_whole_onto_one_sheet_side(tmp_path, builder):
    """The spread is one landscape page covering two slots, and those two
    slots are one sheet side — so it must be placed once at full width, not
    sliced in half or drawn twice."""
    from pypdf import PdfReader

    result = generate_workbook(
        destination="Pelion",
        itinerary=ITINERARY,
        page_count=12,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    spread = next(page for page in result.workbook.pages if page.is_spread)
    sheets = PdfReader(str(result.artifacts.workbook_booklet_pdf)).pages

    # Innermost sheet, back side — the last printed side.
    text = sheets[-1].extract_text()
    assert f"{spread.number}-{spread.number + 1}" in text
    assert text.count(spread.title) == 1, "the spread must be placed once, not twice"


# -- helpers -------------------------------------------------------------


def _context(builder, **kwargs):
    return generate_workbook(
        destination="Pelion", itinerary=ITINERARY, write=False, builder=builder, **kwargs
    ).bundle.context
