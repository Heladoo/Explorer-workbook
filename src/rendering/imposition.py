"""Booklet imposition: A5 pages → foldable, staplable A4 sheets.

The page PDF that :class:`~src.rendering.pdf_renderer.PdfRenderer` writes is
the book in *reading* order, one A5 page after another. That is the right file
to read on a screen or hand to a print shop, and the wrong one to send to a
home printer: printed in order, folding it produces gibberish.

This module writes the second file — the same pages rearranged onto A4
landscape sheets in the order a saddle-stitched booklet actually needs, so the
whole stack can be printed duplex, folded once down the middle and stapled
through the fold.

The arithmetic is the standard saddle-stitch one. A folded sheet carries four
pages, two per side, and the outermost sheet holds the first and last pages of
the book. For an ``N``-page book and sheet ``k`` counting from the outside::

    front of sheet k:  [ N - 2k ][ 2k + 1 ]
    back  of sheet k:  [ 2k + 2 ][ N - 2k - 1 ]

with the pair written left-to-right as they sit on the sheet. Two consequences
worth naming, because both are easy to get wrong and expensive to discover
after printing thirty copies:

* **The centre spread falls out for free.** The innermost sheet is
  ``k = N/4 - 1``, whose back works out to exactly ``[N/2, N/2 + 1]`` — the
  centre pair. That is *why* a double-page spread can only live at the centre
  of a booklet: it is the only page pair that shares one side of one sheet.
  See :func:`~src.agents.planner.WorkbookPlanner._centrefold`.

* **A right-bound book mirrors every pair.** Hebrew opens from the right, so
  its page 1 is the left-hand page of the first spread rather than the right.
  Every ``[left][right]`` above swaps. Nothing else changes: the sheet order,
  the fold and the staple are identical.

``pypdf`` does the page-placement itself; this module owns the ordering, the
geometry and the fold/staple marks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.rendering.formats import PageFormat

logger = logging.getLogger(__name__)

INSTALL_HINT = (
    "Booklet imposition needs pypdf: pip install pypdf (or install this "
    "project's 'pdf' extra, which pulls in both pypdf and playwright)."
)

#: PDF user-space units per millimetre. PDF measures in points, 72 to the inch.
_PT_PER_MM = 72.0 / 25.4

#: How long the fold/staple marks are, and how far in from the sheet edge the
#: staple marks sit. Marks are drawn in the sheet's unprintable-ish margin
#: rather than across the page area, so they never cross artwork.
_FOLD_MARK_MM = 4.0
_STAPLE_INSET_MM = 55.0


@dataclass(frozen=True)
class BookletPlan:
    """Which page goes where, before any PDF is touched.

    Pure arithmetic, no I/O — so the ordering can be tested directly rather
    than by rendering a book and reading the result back out of a PDF.
    """

    page_count: int
    binding: str
    #: One ``(left, right)`` pair of 1-based page numbers per printed sheet
    #: side, in the order the sides must be printed: sheet 1 front, sheet 1
    #: back, sheet 2 front, ... ``None`` in either slot means a blank.
    sides: tuple[tuple[int | None, int | None], ...]

    @property
    def sheet_count(self) -> int:
        return len(self.sides) // 2


def plan_booklet(page_count: int, *, binding: str = "left") -> BookletPlan:
    """Work out the sheet order for an ``page_count``-page saddle-stitched book.

    ``binding`` is ``"left"`` for a normally-bound book or ``"right"`` for one
    that opens the other way (Hebrew, Arabic), which mirrors every pair.
    """
    if page_count % 4:
        raise ValueError(
            f"a saddle-stitched booklet needs a multiple of 4 pages, got {page_count}. "
            "One folded sheet carries exactly four pages, so no other length can fold."
        )
    if binding not in ("left", "right"):
        raise ValueError(f"binding must be 'left' or 'right', got {binding!r}")

    sides: list[tuple[int | None, int | None]] = []
    for sheet in range(page_count // 4):
        front = (page_count - 2 * sheet, 2 * sheet + 1)
        back = (2 * sheet + 2, page_count - 2 * sheet - 1)
        if binding == "right":
            front, back = front[::-1], back[::-1]
        sides.append(front)
        sides.append(back)
    return BookletPlan(page_count=page_count, binding=binding, sides=tuple(sides))


def impose_booklet(
    source: Path | str,
    target: Path | str,
    *,
    page_format: PageFormat,
    page_count: int,
    binding: str = "left",
    fold_marks: bool = True,
) -> Path:
    """Rearrange ``source``'s A5 pages onto A4 sheets and write ``target``.

    ``page_count`` is the book's *slot* count (``Workbook.page_count``), which
    is not ``len(reader.pages)`` when the book contains a centre spread: the
    spread is one physical PDF page covering two slots. It is mapped back onto
    both of its slots here, and because those two slots are always the two
    halves of one sheet side, it is placed whole rather than sliced.
    """
    try:
        from pypdf import PageObject, PdfReader, PdfWriter, Transformation
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise RuntimeError(INSTALL_HINT) from exc

    source, target = Path(source), Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    if page_format.sheet_width_mm is None or page_format.sheet_height_mm is None:
        raise ValueError(f"{page_format.key} is not imposed onto sheets")

    reader = PdfReader(str(source))
    slots = _slots(reader, page_count)
    plan = plan_booklet(page_count, binding=binding)

    sheet_w = page_format.sheet_width_mm * _PT_PER_MM
    sheet_h = page_format.sheet_height_mm * _PT_PER_MM
    fold = sheet_w / 2

    writer = PdfWriter()
    for left, right in plan.sides:
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)
        # A spread occupies both slots of this side with one page that is
        # already the full width: place it once, centred, not twice.
        if left and right and slots[left] is slots[right]:
            sheet.merge_transformed_page(
                slots[left], _centre(slots[left], sheet_w, sheet_h, Transformation)
            )
        else:
            # Register both pages against the fold rather than against the
            # sheet's outer edges. The fold is the one line that has to be
            # exact — it is where the two halves must meet and where the
            # staple goes — so any difference between the rendered page size
            # and half a sheet is pushed outwards, to the trimmed edge, where
            # a fraction of a millimetre costs nothing.
            for number, align_right in ((left, True), (right, False)):
                page = slots.get(number) if number else None
                if page is None:
                    continue
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                tx = fold - width if align_right else fold
                sheet.merge_transformed_page(
                    page, Transformation().translate(tx=tx, ty=(sheet_h - height) / 2)
                )
        # Add first, draw second: add_page() clones the page into the writer,
        # and marks drawn onto the detached original are cloned along with it
        # in a form the cloner cannot resolve.
        added = writer.add_page(sheet)
        if fold_marks:
            _draw_fold_marks(writer, added, sheet_w, sheet_h)

    with open(target, "wb") as handle:
        writer.write(handle)
    logger.info(
        "imposed %d pages onto %d %s-bound sheets: %s",
        page_count,
        plan.sheet_count,
        binding,
        target,
    )
    return target


# -- internals -----------------------------------------------------------


def _centre(page, sheet_w: float, sheet_h: float, transformation):
    """Centre a page on the sheet — used for the full-width centre spread."""
    return transformation().translate(
        tx=(sheet_w - float(page.mediabox.width)) / 2,
        ty=(sheet_h - float(page.mediabox.height)) / 2,
    )


def _slots(reader, page_count: int) -> dict[int, object]:
    """Map every 1-based page slot to the PDF page that carries it.

    A centre spread is one PDF page standing in for two slots, so both of its
    slot numbers map to the *same* object — which is what lets
    :func:`impose_booklet` recognise it by identity and place it whole.

    Spreads are detected by width rather than by being told where they are:
    the PDF is the authority on what it actually contains, and a page twice
    the width of its neighbours is a spread no matter which activity produced
    it or what the plan claimed.
    """
    pages = list(reader.pages)
    widths = [float(page.mediabox.width) for page in pages]
    if not widths:
        raise ValueError("cannot impose an empty PDF")

    narrowest = min(widths)
    slots: dict[int, object] = {}
    number = 1
    for page, width in zip(pages, widths):
        span = 2 if width > narrowest * 1.5 else 1
        for _ in range(span):
            slots[number] = page
            number += 1

    filled = number - 1
    if filled != page_count:
        raise ValueError(
            f"{source_name(reader)} covers {filled} page slots but the book is "
            f"{page_count} pages. The imposed sheets would be wrong, so nothing "
            "was written."
        )
    return slots


def source_name(reader) -> str:
    stream = getattr(reader, "stream", None)
    return getattr(stream, "name", "the rendered PDF")


def _draw_fold_marks(writer, sheet, width: float, height: float) -> None:
    """Short rules at the fold, and ticks where the staples go.

    Drawn only in the top and bottom few millimetres of the sheet so they
    cannot cross a page's own content, and short enough to disappear into the
    fold once the sheet is folded. Two staples at +/-55mm from the centre is
    the standard saddle-stitch position for A5.
    """
    centre = width / 2
    mark = _FOLD_MARK_MM * _PT_PER_MM
    inset = _STAPLE_INSET_MM * _PT_PER_MM

    segments = [
        # The fold itself, ticked at both ends of the sheet.
        (centre, 0.0, centre, mark),
        (centre, height - mark, centre, height),
    ]
    # Staple positions, as short ticks either side of the fold's midpoint.
    for offset in (-inset, inset):
        y = height / 2 + offset
        if 0 < y < height:
            segments.append((centre - mark / 2, y, centre + mark / 2, y))

    from pypdf.generic import ContentStream

    # `q ... Q` brackets the whole thing so the thin grey stroke state cannot
    # leak into anything drawn after it.
    content = (
        "q 0.5 w 0.6 G\n"
        + "".join(f"{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S\n" for x1, y1, x2, y2 in segments)
        + "Q\n"
    )
    stream = ContentStream(sheet.get_contents(), writer)
    stream.set_data(stream.get_data() + content.encode("ascii"))
    sheet.replace_contents(stream)


__all__ = ["BookletPlan", "impose_booklet", "plan_booklet"]
