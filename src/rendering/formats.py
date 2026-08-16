"""What physical shape the printed book takes.

The layout stage renders the same workbook into one of two page formats. A
format is *only* geometry and the type scale that geometry needs — no rule in
``book.css`` is duplicated per format, because everything there sizes itself
against the tokens declared here (``--page-width``, ``--page-height``, the
``--size-*`` ladder). See ``src/templates/pdf/page-a5.css`` and ``page-a4.css``.

``a5-booklet`` is the default: A5 pages, printed two-up on A4 sheets, folded
down the middle and stapled through the fold. ``a4-portrait`` is the original
one-activity-per-A4-sheet layout, kept because it needs no folding, no stapler
and no duplex printer — the format to reach for when someone just wants to hit
print.

The A5 pages are laid out *natively* at A5 rather than being an A4 book scaled
to 70.7%: a shrunk A4 page takes 11.5pt body copy down to 8.1pt and its writing
lines with it, which is below what the children this book is for can actually
write on. The type scale in ``page-a5.css`` is therefore re-tuned, not scaled —
body copy barely moves, display sizes absorb the difference.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The book lengths offered on the product surfaces (CLI, web form).
#:
#: Every one is a multiple of 4 because that is what a saddle-stitched booklet
#: is made of: one folded A4 sheet carries four A5 pages, so a foldable book
#: can only ever be 8, 12, 16, ... pages long. Deliberately a short menu rather
#: than "any multiple of 4" — see ``docs`` in the README.
#:
#: Note this constrains the *offered* lengths, not what the planner can do.
#: ``WorkbookPlanner`` still plans any count (its tests rely on that, and the
#: A4 format has no multiple-of-4 constraint at all); only building booklet
#: sheets genuinely requires the arithmetic to work out, and that is enforced
#: in :mod:`src.rendering.imposition` where it actually matters.
PAGE_COUNT_CHOICES = (8, 12, 16)

DEFAULT_PAGE_COUNT = 12


@dataclass(frozen=True)
class PageFormat:
    """One physical page format the book can be laid out in."""

    #: Stable identifier used by the CLI, the web form and ``workbook.json``.
    key: str
    #: Human-readable, for CLI help and the web form.
    label: str
    #: The format's geometry + type scale stylesheet, loaded ahead of
    #: ``book.css`` (which carries every other rule, for both formats).
    css_filename: str
    #: Finished page size in mm. Used to verify rendered output and to lay
    #: pages out on a sheet; the authoritative copy for *rendering* is the
    #: ``@page size`` in the stylesheet above, and a test pins the two together.
    page_width_mm: float
    page_height_mm: float
    #: Whether ``--pdf`` also writes an imposed, fold-and-staple sheet PDF
    #: alongside the page-per-page one.
    booklet: bool
    #: Whether this format can carry a double-page centre spread. Only a
    #: booklet can: a spread is two facing pages on one side of one sheet,
    #: which is a fact about the folded object, not about the page size.
    allows_spread: bool
    #: Outer (trimmed edge) and inner (fold/gutter) margins, in mm. Mirrors
    #: the ``@page :left`` / ``:right`` rules in the stylesheet; the renderer
    #: re-emits them flipped for a right-bound (RTL) book, which ``@page``
    #: cannot express on its own since it has no access to the document's
    #: direction. See ``HtmlRenderer._binding_css``.
    margin_outer_mm: float
    margin_inner_mm: float
    #: The physical sheet two pages are imposed onto, in mm. ``None`` for a
    #: format that is printed one page per sheet.
    #:
    #: Deliberately *not* ``page_width_mm * 2``: two A5 portraits measure
    #: 296mm and A4 landscape is 297mm. Imposing onto 296 would hand the
    #: printer a sheet a millimetre off its actual paper, which it answers by
    #: scaling or offsetting the whole thing. The sheet is the paper's size;
    #: the millimetre of A-series slack is absorbed at the outer edges, which
    #: is where a trimmed-and-handled edge can afford it — never at the fold.
    sheet_width_mm: float | None = None
    sheet_height_mm: float | None = None

    @property
    def spread_width_mm(self) -> float:
        """A centre spread is two facing pages side by side."""
        return self.page_width_mm * 2


#: A5 portrait pages, imposed two-up on A4 and folded. Two A5 portraits side by
#: side measure 296mm against A4 landscape's 297mm — the 1mm is A-series
#: rounding, and the spread's ``@page`` size below absorbs it rather than
#: leaving a hairline of unprintable sheet down the fold.
A5_BOOKLET = PageFormat(
    key="a5-booklet",
    label="A5 booklet (two pages per A4 sheet, folded and stapled)",
    css_filename="page-a5.css",
    page_width_mm=148.0,
    page_height_mm=210.0,
    booklet=True,
    allows_spread=True,
    margin_outer_mm=9.0,
    margin_inner_mm=12.0,
    sheet_width_mm=297.0,
    sheet_height_mm=210.0,
)

#: One activity per A4 sheet — the original format. No folding, no stapler, no
#: duplex printer, and no multiple-of-4 constraint on the page count.
A4_PORTRAIT = PageFormat(
    key="a4-portrait",
    label="A4 portrait (one page per sheet, no folding)",
    css_filename="page-a4.css",
    page_width_mm=210.0,
    page_height_mm=297.0,
    booklet=False,
    allows_spread=False,
    margin_outer_mm=12.0,
    margin_inner_mm=16.0,
)

FORMATS: dict[str, PageFormat] = {fmt.key: fmt for fmt in (A5_BOOKLET, A4_PORTRAIT)}

#: A5 booklet, because that is what the book is *for* — a thing a child holds
#: on a trip. A4 stays one flag away.
DEFAULT_FORMAT = A5_BOOKLET


def get_format(key: str | PageFormat | None) -> PageFormat:
    """Resolve a format key, defaulting when it is ``None``.

    Accepts a :class:`PageFormat` unchanged so callers can pass either without
    every call site having to know which it holds.
    """
    if key is None:
        return DEFAULT_FORMAT
    if isinstance(key, PageFormat):
        return key
    try:
        return FORMATS[key]
    except KeyError as exc:
        known = ", ".join(sorted(FORMATS))
        raise ValueError(f"unknown page format {key!r}; known: {known}") from exc


__all__ = [
    "A4_PORTRAIT",
    "A5_BOOKLET",
    "DEFAULT_FORMAT",
    "DEFAULT_PAGE_COUNT",
    "FORMATS",
    "PAGE_COUNT_CHOICES",
    "PageFormat",
    "get_format",
]
