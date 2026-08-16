"""Extension points for the stages that consume a finished workbook.

An image backend consumes the prompts this system produces; a document renderer
consumes the workbook structure. Neither needs any change to the agents or the
activities, which is the point of stating them as Protocols here.

``src.image_backends.openrouter`` and ``src.rendering.pdf_renderer`` are the
shipped implementations; both stages stay optional, and a book generated
without either still prints with labelled placeholders.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from src.models.context import WorkbookContext
from src.models.page import Page, SymbolBrief
from src.models.workbook import Workbook


@runtime_checkable
class ImageBackend(Protocol):
    """Turns a page's ``image_prompt`` into an actual image.

    Implement this to replace prompt files with generated artwork: the prompt
    is already final, so an implementation only has to call an image model and
    return where it put the result.
    """

    name: str

    def generate(self, page: Page, context: WorkbookContext, *, output_dir: Path) -> Path:
        """Render ``page.image_prompt`` and return the path to the image file."""


@runtime_checkable
class SymbolImageBackend(Protocol):
    """Optionally implemented by an :class:`ImageBackend` that can draw symbols.

    A page laid out as a table of pictures (the scavenger hunt) needs one small
    drawing per cell rather than one illustration. Backends are not required to
    support this — ``src.image_backends.runner`` checks for the method and
    leaves placeholder cells when it is missing.

    A symbol's prompt names no destination, no characters and no house style, so
    an implementation should keep the request identical everywhere: that is what
    lets one drawing be cached and reused across pages, languages and books.
    """

    name: str

    def generate_symbol(
        self, symbol: SymbolBrief, context: WorkbookContext, *, output_dir: Path
    ) -> Path:
        """Render ``symbol.prompt`` and return the path to the image file."""


@runtime_checkable
class DocumentRenderer(Protocol):
    """Lays the workbook out as a printable document.

    Implement this for PDF output. Everything it needs is already in the
    workbook: page order, instructions, per-page metadata (checkbox counts,
    maze grids, quiz answers) and the illustration for each page.
    """

    name: str

    def render(
        self,
        workbook: Workbook,
        context: WorkbookContext,
        *,
        images: dict[int, Path] | None = None,
        output_path: Path,
    ) -> Path:
        """Write the document and return its path."""
