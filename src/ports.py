"""Extension points for the stages the MVP deliberately stops short of.

Nothing implements these yet. They exist so the shape of the next two features
is settled: an image backend consumes the prompts this system produces, and a
document renderer consumes the workbook structure. Neither needs any change to
the agents or the activities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from src.models.context import WorkbookContext
from src.models.page import Page
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
