"""The only module that touches the filesystem.

Keeping I/O here means the generators and agents stay pure and testable, and a
future PDF or image stage writes through the same door.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.pipeline import WorkbookBundle

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_ROOT = Path("output")


@dataclass(frozen=True)
class WrittenArtifacts:
    """Where everything ended up."""

    output_dir: Path
    workbook_json: Path
    workbook_md: Path
    prompt_files: tuple[Path, ...]
    workbook_html: Path | None = None
    workbook_pdf: Path | None = None

    def as_list(self) -> tuple[Path, ...]:
        extra = tuple(path for path in (self.workbook_html, self.workbook_pdf) if path)
        return (self.workbook_json, self.workbook_md, *self.prompt_files, *extra)


def write_bundle(
    bundle: WorkbookBundle,
    output_dir: Path | str,
    *,
    html: bool = False,
    pdf: bool = False,
    images: dict[int, Path] | None = None,
) -> WrittenArtifacts:
    """Write ``workbook.json``, ``workbook.md`` and ``prompts/*.md``.

    ``html`` and ``pdf`` additionally lay the book out for print. ``images``
    maps page numbers to illustration files; pages without one get a
    placeholder frame naming their prompt file.
    """
    root = Path(output_dir)
    prompts_dir = root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    json_path = root / "workbook.json"
    json_path.write_text(bundle.json, encoding="utf-8")

    md_path = root / "workbook.md"
    md_path.write_text(bundle.markdown, encoding="utf-8")

    written: list[Path] = []
    for filename, content in sorted(bundle.prompts.items()):
        path = prompts_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)

    _warn_about_stale(prompts_dir, {path.name for path in written})

    html_path: Path | None = None
    pdf_path: Path | None = None
    if html or pdf:
        if bundle.context is None:
            raise ValueError("laying the book out for print needs the bundle's context")
        if pdf:
            # The PDF renderer writes the HTML it prints from, so one pass covers both.
            from src.rendering.pdf_renderer import PdfRenderer

            pdf_path = PdfRenderer(keep_html=True).render(
                bundle.workbook, bundle.context, images=images, output_path=root / "workbook.pdf"
            )
            html_path = root / "workbook.html"
        else:
            from src.rendering.html_renderer import HtmlRenderer

            html_path = root / "workbook.html"
            html_path.write_text(
                HtmlRenderer().render(bundle.workbook, bundle.context, images=images),
                encoding="utf-8",
            )

    return WrittenArtifacts(
        output_dir=root,
        workbook_json=json_path,
        workbook_md=md_path,
        prompt_files=tuple(written),
        workbook_html=html_path,
        workbook_pdf=pdf_path,
    )


def default_output_dir(destination_slug: str, root: Path | str | None = None) -> Path:
    """``output/<destination-slug>`` unless the caller says otherwise."""
    return Path(root or DEFAULT_OUTPUT_ROOT) / destination_slug


def _warn_about_stale(prompts_dir: Path, current: set[str]) -> None:
    """Point out leftovers from an earlier, longer run rather than deleting them."""
    stale = sorted(
        path.name for path in prompts_dir.glob("*.md") if path.name not in current
    )
    if stale:
        logger.warning(
            "%s contains %d prompt file(s) from an earlier run, left untouched: %s",
            prompts_dir,
            len(stale),
            ", ".join(stale),
        )
