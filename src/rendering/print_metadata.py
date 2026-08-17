"""Reads back what a rendered book's own document says about how to print it.

The in-browser editor (the inline script in ``book.html.tmpl``) lets someone
edit text or swap in photos, then hands the *edited* document back to the
local server to print — there is no ``Workbook``/``WorkbookContext`` any more,
only markup. ``HtmlRenderer`` writes the page format, slot count and reading
direction it rendered with onto ``<html>`` itself, so the print pipeline
(``PdfRenderer.render_html`` + ``impose_booklet``) can pick the same format
and imposition it would have used the first time, entirely from the document
the browser sends back.

Those ``data-page-*`` attributes only exist on documents rendered *after* this
module was added, though, and every book generated before then — including
any already sitting in ``output/`` or exported to a standalone ``.html`` file
via the editor's own "Save workbook" button — has neither. Rather than refuse
to print those, :func:`read_print_metadata` falls back to sniffing the same
two facts from markup that has been stable for much longer: which format's
``@page`` rule is present in the inlined CSS, and how many ``<section
class="page ...">`` elements (plus one extra per centre spread) the document
actually contains.
"""

from __future__ import annotations

import html as html_module
import re
from html.parser import HTMLParser

from src.rendering.formats import A4_PORTRAIT, A5_BOOKLET, PageFormat, get_format

#: Literal text from each format's own ``@page`` rule (page-a5.css /
#: page-a4.css) — present in every rendered document regardless of age,
#: since neither stylesheet has ever declared its size any other way.
_FORMAT_SNIFFS = (
    ("size: A5 portrait", A5_BOOKLET),
    ("size: A4 portrait", A4_PORTRAIT),
)

_SECTION_RE = re.compile(r'<section class="page ([^"]*)"')
_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)


class PrintMetadataError(ValueError):
    """The document has nothing (or nothing valid) to print it from."""


class _HtmlTagParser(HTMLParser):
    """Captures just the first <html> tag's attributes, then ignores the rest."""

    def __init__(self) -> None:
        super().__init__()
        self.attrs: dict[str, str | None] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "html" and self.attrs is None:
            self.attrs = dict(attrs)


def read_print_metadata(html_text: str) -> tuple[PageFormat, int, str, str]:
    """``(page_format, page_count, binding, title)`` for printing ``html_text``.

    ``page_count`` is the book's *slot* count (``Workbook.page_count``, what
    ``impose_booklet`` expects), not the number of rendered sections — a
    centre spread is one section covering two slots.

    Raises :class:`PrintMetadataError` if ``html_text`` was not a document
    this project rendered at all — no ``<html>`` tag, or a format/count
    neither the ``data-page-*`` attributes nor the markup fallback could
    make sense of.
    """
    parser = _HtmlTagParser()
    parser.feed(html_text)
    attrs = parser.attrs
    if attrs is None:
        raise PrintMetadataError("no <html> tag found in the document")

    page_format = _read_format(attrs, html_text)
    page_count = _read_page_count(attrs, html_text)

    # Which edge the staple goes through is a property of the language, not
    # the paper — see imposition.plan_booklet. Mirrors output_writer._impose's
    # own "dir == rtl -> right" rule, just read back from the markup instead
    # of from Strings.direction, since there is no language code here either.
    binding = "right" if attrs.get("dir") == "rtl" else "left"
    title = _read_title(html_text)
    return page_format, page_count, binding, title


def _read_format(attrs: dict[str, str | None], html_text: str) -> PageFormat:
    format_key = attrs.get("data-page-format")
    if format_key:
        try:
            return get_format(format_key)
        except ValueError as exc:
            raise PrintMetadataError(str(exc)) from exc

    for needle, fmt in _FORMAT_SNIFFS:
        if needle in html_text:
            return fmt
    raise PrintMetadataError(
        "couldn't tell which page format this document is — no data-page-format "
        "attribute and no recognisable @page size rule in its CSS"
    )


def _read_page_count(attrs: dict[str, str | None], html_text: str) -> int:
    count_raw = attrs.get("data-page-count")
    if count_raw:
        try:
            return int(count_raw)
        except ValueError as exc:
            raise PrintMetadataError(f"data-page-count is not a number: {count_raw!r}") from exc

    slots = 0
    for classes in _SECTION_RE.findall(html_text):
        names = classes.split()
        if "toc" in names:
            continue
        slots += 2 if "page-spread" in names else 1
    if not slots:
        raise PrintMetadataError(
            "couldn't tell how many pages this document has — no data-page-count "
            "attribute and no <section class=\"page ...\"> elements to count"
        )
    return slots


def _read_title(html_text: str) -> str:
    match = _TITLE_RE.search(html_text)
    return html_module.unescape(match.group(1)).strip() if match else ""


__all__ = ["PrintMetadataError", "read_print_metadata"]
