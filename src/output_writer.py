"""The only module that touches the filesystem.

Keeping I/O here means the generators and agents stay pure and testable, and a
future PDF or image stage writes through the same door.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.pipeline import WorkbookBundle
from src.rendering.formats import PageFormat, get_format
from src.strings import strings_for
from src.symbol_art import artwork_for

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
    #: The same book imposed onto fold-and-staple sheets. Written alongside
    #: ``workbook_pdf`` for a booklet format, never instead of it: the page
    #: PDF is the one to read on screen or hand to a print shop, and this one
    #: is the one to send to a home printer. See :mod:`src.rendering.imposition`.
    workbook_booklet_pdf: Path | None = None

    def as_list(self) -> tuple[Path, ...]:
        extra = tuple(
            path
            for path in (self.workbook_html, self.workbook_pdf, self.workbook_booklet_pdf)
            if path
        )
        return (self.workbook_json, self.workbook_md, *self.prompt_files, *extra)


def write_bundle(
    bundle: WorkbookBundle,
    output_dir: Path | str,
    *,
    html: bool = False,
    pdf: bool = False,
    images: dict[int, Path] | None = None,
    symbol_images: dict[str, Path] | None = None,
    ink_saver: bool = False,
    page_format: str | PageFormat | None = None,
    booklet: bool = True,
) -> WrittenArtifacts:
    """Write ``workbook.json``, ``workbook.md`` and ``prompts/*.md``.

    ``html`` and ``pdf`` additionally lay the book out for print. ``images``
    maps page numbers to illustration files; pages without one get a
    placeholder frame naming their prompt file. ``symbol_images`` maps a symbol
    slug to its drawing, for pages laid out as a table of pictures. ``ink_saver``
    flattens the print layout's brand colors to grayscale, for cheap home
    printing.

    ``page_format`` picks the physical page format; it defaults to the one the
    book was planned for (``context.page_format``), so a caller that plans an
    A4 book and then lays it out cannot accidentally get A5 geometry wrapped
    around a plan that has no centre spread in it.

    ``booklet`` additionally writes the imposed, fold-and-staple sheet PDF for
    a booklet format. Set it ``False`` to skip that second file — the page PDF
    is unaffected either way.
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
        # Symbol prompts live in ``prompts/symbols/``, so a name may be nested.
        path = prompts_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)

    _warn_about_stale(prompts_dir, {path.name for path in written})

    html_path: Path | None = None
    pdf_path: Path | None = None
    booklet_path: Path | None = None
    if html or pdf:
        if bundle.context is None:
            raise ValueError("laying the book out for print needs the bundle's context")
        fmt = get_format(page_format if page_format is not None else bundle.context.page_format)
        # Symbol artwork is checked into the repo, not generated per book, so
        # the print layout picks it up on every run — not only on the runs that
        # passed ``--generate-images``. Anything the caller generated during
        # *this* run is layered on top.
        art = artwork_for(bundle.workbook, overrides=symbol_images)
        if pdf:
            # The PDF renderer writes the HTML it prints from, so one pass covers both.
            from src.rendering.html_renderer import HtmlRenderer
            from src.rendering.pdf_renderer import PdfRenderer

            pdf_path = PdfRenderer(
                HtmlRenderer(ink_saver=ink_saver, include_contents=False, page_format=fmt),
                keep_html=True,
            ).render(
                bundle.workbook,
                bundle.context,
                images=images,
                symbol_images=art.images,
                symbol_cutouts=art.cutouts,
                symbol_shadows=art.silhouettes,
                output_path=root / "workbook.pdf",
            )
            html_path = root / "workbook.html"
            if booklet:
                booklet_path = _impose(bundle, fmt, pdf_path, root / "workbook-booklet.pdf")
        else:
            from src.rendering.html_renderer import HtmlRenderer

            html_path = root / "workbook.html"
            html_path.write_text(
                HtmlRenderer(ink_saver=ink_saver, page_format=fmt).render(
                    bundle.workbook,
                    bundle.context,
                    images=images,
                    symbol_images=art.images,
                    symbol_cutouts=art.cutouts,
                    symbol_shadows=art.silhouettes,
                ),
                encoding="utf-8",
            )

    return WrittenArtifacts(
        output_dir=root,
        workbook_json=json_path,
        workbook_md=md_path,
        prompt_files=tuple(written),
        workbook_html=html_path,
        workbook_pdf=pdf_path,
        workbook_booklet_pdf=booklet_path,
    )


def _impose(
    bundle: WorkbookBundle, fmt: PageFormat, pdf_path: Path, target: Path
) -> Path | None:
    """Write the fold-and-staple sheet PDF, or explain why there isn't one.

    Never fatal. The page PDF is already written and is a perfectly good book
    by the time this runs, so a length that cannot fold, or a missing pypdf,
    costs the *second* file and a warning — not the run.
    """
    if not fmt.booklet:
        return None
    page_count = bundle.workbook.page_count
    if page_count % 4:
        logger.warning(
            "no fold-and-staple sheets written: %d pages is not a multiple of 4, so the "
            "book cannot be saddle-stitched. workbook.pdf is unaffected.",
            page_count,
        )
        return None

    from src.rendering.imposition import impose_booklet

    # Which edge the staple goes through is a property of the language, not of
    # the paper: a Hebrew book opens from the right, so every page pair on
    # every sheet mirrors. See imposition.plan_booklet.
    binding = "right" if strings_for(bundle.workbook.language).direction == "rtl" else "left"
    try:
        return impose_booklet(
            pdf_path, target, page_format=fmt, page_count=page_count, binding=binding
        )
    except (RuntimeError, ValueError) as exc:
        logger.warning("no fold-and-staple sheets written: %s", exc)
        return None


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
