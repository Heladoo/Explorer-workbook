"""Lays the workbook out as a printable HTML document.

This is the layout stage the MVP stopped short of: it consumes exactly what
``workbook.json`` already contains and adds no content of its own. The PDF
renderer prints this document; opening it in a browser gives the same pages.
"""

from __future__ import annotations

from pathlib import Path

from src.models.context import WorkbookContext
from src.models.workbook import Workbook
from src.rendering.layouts import LayoutContext, build_body
from src.rendering.templates import TemplateSet
from src.strings import strings_for


class HtmlRenderer:
    """Workbook + context → one self-contained HTML file, print styled for A4."""

    name = "html"

    def __init__(
        self,
        template_dir: Path | str | None = None,
        *,
        include_contents: bool = True,
        css_filename: str = "book.css",
    ) -> None:
        self.templates = TemplateSet(template_dir)
        self.include_contents = include_contents
        self.css_filename = css_filename

    def render(
        self,
        workbook: Workbook,
        context: WorkbookContext,
        *,
        images: dict[int, Path] | None = None,
    ) -> str:
        """Render the whole book.

        ``images`` maps a page number to an illustration file. Pages without
        one get a labelled placeholder frame naming their prompt file, so the
        book is printable before any artwork exists.
        """
        strings = strings_for(context.language)
        layout_context = LayoutContext(
            templates=self.templates,
            context=context,
            strings=strings,
            images={
                number: Path(path).resolve().as_uri()
                for number, path in (images or {}).items()
            },
        )

        pages = "\n".join(
            self.templates.render(
                "page",
                page_class=f"page-{page.type}",
                number=page.number,
                title=page.title,
                instructions=page.instructions,
                destination=workbook.destination,
                prompt_note=self._prompt_note(page, layout_context),
                body=build_body(layout_context, page),
            )
            for page in workbook.pages
        )

        return self.templates.render(
            "book",
            language=workbook.language,
            title=workbook.title,
            css=self.templates.read_asset(self.css_filename),
            contents=self._contents(workbook, strings) if self.include_contents else "",
            pages=pages,
        )

    def _prompt_note(self, page, layout_context: LayoutContext) -> str:
        """Name the prompt file until the page's artwork actually exists.

        Pages that lay their illustrations out cell by cell (fact cards, quiz
        rows, matching columns) have nowhere else to say where their picture
        comes from, and the note disappears once an image is supplied.
        """
        if page.number in layout_context.images:
            return ""
        return f"prompts/{page.prompt_filename}"

    def _contents(self, workbook: Workbook, strings) -> str:
        rows = "\n".join(
            self.templates.render(
                "toc_row",
                number=page.number,
                title=page.title,
                type=page.type.replace("_", " "),
                age=page.estimated_age or "—",
            )
            for page in workbook.pages
        )
        return self.templates.render(
            "toc",
            title=workbook.title,
            subtitle=strings.text("pdf.contents"),
            destination=workbook.destination,
            rows=rows,
        )
