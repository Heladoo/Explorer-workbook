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
    """Workbook + context → one self-contained HTML file, print styled for A4."""

    name = "html"

    def __init__(
        self,
        template_dir: Path | str | None = None,
        *,
        include_contents: bool = True,
        css_filename: str = "book.css",
        ink_saver: bool = False,
    ) -> None:
        self.templates = TemplateSet(template_dir)
        self.include_contents = include_contents
        self.css_filename = css_filename
        #: Flattens the brand palette to grayscale for cheap home printing —
        #: see the ``.ink-saver`` token overrides in book.css.
        self.ink_saver = ink_saver

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
                page_class=f"page-{page.type}",
                number=page.number,
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

        return self.templates.render(
            "book",
            language=workbook.language,
            direction=strings.direction,
            title=workbook.title,
            fonts=self.templates.font_faces(scripts=needed_scripts),
            css=self.templates.read_asset(self.css_filename),
            body_class="ink-saver" if self.ink_saver else "",
            contents=contents,
            pages=pages,
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
