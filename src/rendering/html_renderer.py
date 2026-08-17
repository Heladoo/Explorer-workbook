"""Lays the workbook out as a printable HTML document.

This is the layout stage the MVP stopped short of: it consumes exactly what
``workbook.json`` already contains and adds no content of its own. The PDF
renderer prints this document; opening it in a browser gives the same pages.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from src import fonts
from src.models.context import WorkbookContext
from src.models.workbook import Workbook
from src.rendering.formats import PageFormat, get_format
from src.rendering.layouts import LayoutContext, build_body
from src.rendering.templates import TemplateSet
from src.strings import strings_for

#: Activity types whose instructions text quotes generated puzzle data
#: word-for-word — the word search spells out its own answer list ("Find and
#: circle each one: BOAT, BRIDGE, ...") right inside the sentence. Clicking
#: the pencil on that text edits the sentence, not the grid or the metadata
#: the answer list came from, so a typo'd or deleted word there would
#: silently stop matching what's actually hidden in the puzzle. Excluded
#: from click-to-edit for exactly that reason; every other page's
#: instructions is just prose, safe to reword freely.
_INSTRUCTIONS_LOCKED = frozenset({"word_search"})


def _data_uri(path: Path | str) -> str:
    """Inline a page/symbol image as base64 so the HTML stays self-contained.

    A ``file://`` reference only loads when the document itself is opened as
    a local file — a browser refuses to fetch it from a page served over
    http(s), which is exactly how the web form's result page shows this HTML
    (``/files/...`` and ``/go/...``), so every image silently failed there.
    """
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class HtmlRenderer:
    """Workbook + context → one self-contained HTML file, print styled.

    The page format (A5 booklet by default, A4 portrait on request) selects a
    small geometry stylesheet that is emitted *ahead* of ``book.css``; every
    rule in ``book.css`` sizes itself against the tokens that file declares.
    See :mod:`src.rendering.formats`.
    """

    name = "html"

    def __init__(
        self,
        template_dir: Path | str | None = None,
        *,
        include_contents: bool = True,
        css_filename: str = "book.css",
        ink_saver: bool = False,
        page_format: str | PageFormat | None = None,
    ) -> None:
        self.templates = TemplateSet(template_dir)
        self.include_contents = include_contents
        self.css_filename = css_filename
        #: Flattens the brand palette to grayscale for cheap home printing —
        #: see the ``.ink-saver`` token overrides in book.css.
        self.ink_saver = ink_saver
        self.page_format = get_format(page_format)

    def render(
        self,
        workbook: Workbook,
        context: WorkbookContext,
        *,
        images: dict[int, Path] | None = None,
        symbol_images: dict[str, Path] | None = None,
        symbol_cutouts: dict[str, Path] | None = None,
        symbol_shadows: dict[str, Path] | None = None,
    ) -> str:
        """Render the whole book.

        ``images`` maps a page number to an illustration file. Pages without
        one get a labelled placeholder frame naming their prompt file, so the
        book is printable before any artwork exists.

        ``symbol_images`` maps a symbol slug to its drawing, for pages that lay
        their artwork out cell by cell. It is keyed by symbol rather than page
        because one drawing of a stop sign serves every page that asks for one.

        ``symbol_cutouts`` and ``symbol_shadows`` are the derived variants of
        that same drawing — cut out of its paper, and filled solid as a shadow
        — which the matching page needs and every other page ignores. See
        :mod:`src.symbol_art`.
        """
        strings = strings_for(context.language)

        def as_data_uris(paths: dict[str, Path] | None) -> dict[str, str]:
            return {key: _data_uri(path) for key, path in (paths or {}).items()}

        layout_context = LayoutContext(
            templates=self.templates,
            context=context,
            strings=strings,
            images={number: _data_uri(path) for number, path in (images or {}).items()},
            symbol_images=as_data_uris(symbol_images),
            symbol_cutouts=as_data_uris(symbol_cutouts),
            symbol_shadows=as_data_uris(symbol_shadows),
        )

        pages = "\n".join(
            self.templates.render(
                "page",
                page_class=self._page_class(page),
                number=page.number,
                number_label=self._page_label(page),
                title=page.title,
                instructions=page.instructions,
                instructions_edit_class="" if page.type in _INSTRUCTIONS_LOCKED else " t-edit",
                body=build_body(layout_context, page),
            )
            for page in workbook.pages
        )

        contents = self._contents(workbook, strings) if self.include_contents else ""
        # Scanning the rendered markup itself, rather than trusting
        # ``workbook.language`` or a destination's declared country, is the
        # point: no character can reach the printed page without its script
        # being detected here, whatever activity or translation put it
        # there. See src/fonts.py::scripts_in.
        needed_scripts = fonts.scripts_in(pages + contents + workbook.title)

        # Stamped onto <html> as data-page-format/data-page-count so the
        # in-browser editor's "Save as PDF" can hand the *edited* document
        # back to PdfRenderer/impose_booklet with no Workbook in sight — see
        # src/rendering/print_metadata.py.
        return self.templates.render(
            "book",
            language=workbook.language,
            direction=strings.direction,
            title=workbook.title,
            fonts=self.templates.font_faces(scripts=needed_scripts),
            css=self._css(strings.direction),
            body_class="ink-saver" if self.ink_saver else "",
            contents=contents,
            pages=pages,
            page_format=self.page_format.key,
            page_count=workbook.page_count,
        )

    # -- internals -------------------------------------------------------

    def _page_class(self, page) -> str:
        """``page-<type>``, plus ``page-spread`` for the centre spread.

        ``page-spread`` is what attaches the named ``@page spread`` rule (see
        page-a5.css), so this class is load-bearing geometry rather than a
        styling hook — which is also why it is only emitted for a format that
        declares that rule. Marking a page as a spread in a stylesheet that
        has no ``@page spread`` would leave ``page: spread`` dangling and the
        page would silently print at the normal size with a layout built for
        twice the width.
        """
        classes = [f"page-{page.type}"]
        if page.is_spread and self.page_format.allows_spread:
            classes.append("page-spread")
        return " ".join(classes)

    @staticmethod
    def _page_label(page) -> str:
        """What the page-number chip prints: ``6`` — or ``6-7`` for a spread.

        A spread really is two of the reader's pages, and the numbers on
        either side of it jump accordingly, so printing only the first would
        make the book look like it skips a page.
        """
        if not page.is_spread:
            return str(page.number)
        return f"{page.number}-{page.number + page.span - 1}"

    def _css(self, direction: str) -> str:
        """Format geometry, then every other rule, then the binding override."""
        return "\n".join(
            part
            for part in (
                self.templates.read_asset(self.page_format.css_filename),
                self.templates.read_asset(self.css_filename),
                self._binding_css(direction),
            )
            if part
        )

    def _binding_css(self, direction: str) -> str:
        """Flip the inner/outer margins for a right-bound (RTL) book.

        ``@page :left`` and ``:right`` mean the even and odd sheets of the
        print run — a physical property, and Chromium assigns them from page
        order alone with no regard for the document's ``dir``. Which of those
        two carries the *gutter*, though, is not physical: it depends on which
        edge the book is bound on, and a Hebrew book is bound on the right. It
        is a mirror image of a Latin one, so page 1 is the left-hand page of
        the first spread and its inner margin is on its right.

        The format stylesheets are written for a left-bound book, so an RTL
        book gets these two rules appended to swap them back. Without it a
        Hebrew booklet puts its wider margin on the trimmed outer edge and its
        narrow one into the staple.
        """
        if direction != "rtl":
            return ""
        outer = f"{self.page_format.margin_outer_mm:g}mm"
        inner = f"{self.page_format.margin_inner_mm:g}mm"
        return (
            "/* Right-bound (RTL) book: the gutter changes sides. */\n"
            f"@page :left {{ margin-left: {inner}; margin-right: {outer}; }}\n"
            f"@page :right {{ margin-left: {outer}; margin-right: {inner}; }}\n"
        )

    def _contents(self, workbook: Workbook, strings) -> str:
        rows = "\n".join(
            self.templates.render(
                "toc_row",
                number=page.number,
                title=page.title,
                type=page.type.replace("_", " "),
            )
            for page in workbook.pages
        )
        return self.templates.render(
            "toc",
            title=workbook.title,
            subtitle=strings.text("pdf.contents"),
            destination=workbook.destination,
            col_number=strings.text("toc.column_number"),
            col_page=strings.text("toc.column_page"),
            col_activity=strings.text("toc.column_activity"),
            footer_label=strings.text("toc.footer_label"),
            rows=rows,
        )
