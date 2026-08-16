"""Drives an ``ImageBackend`` over a workbook's pages and symbols.

Backend-agnostic: works with ``OpenRouterImageBackend`` or any other
``ImageBackend`` implementation. One page failing to render logs a warning and
is skipped rather than aborting the rest of the book.

Symbols are the interesting case. A scavenger hunt page needs one drawing per
grid cell, but a symbol's prompt mentions no destination, no characters and no
house style — so the same drawing is correct in every book that asks for it.
This module therefore keys symbol artwork by slug, generates each slug at most
once per run, and will reuse a file already sitting in the cache directory
instead of paying for it again.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.models.context import WorkbookContext
from src.models.workbook import Workbook
from src.ports import ImageBackend

logger = logging.getLogger(__name__)


def generate_images(
    workbook: Workbook,
    context: WorkbookContext,
    backend: ImageBackend,
    *,
    output_dir: Path,
) -> dict[int, Path]:
    """Render every page's ``image_prompt`` and return ``{page.number: path}``.

    Pages the backend fails on are omitted, not raised — they print as the
    usual placeholder frame instead of stopping the whole run.
    """
    images: dict[int, Path] = {}
    for page in workbook.pages:
        if not page.image_prompt:
            continue
        try:
            images[page.number] = backend.generate(page, context, output_dir=output_dir)
        except Exception as exc:  # any backend failure: skip this page, keep going
            logger.warning(
                "image generation failed for page %s (%s): %s", page.number, page.type, exc
            )
    return images


def generate_symbol_images(
    workbook: Workbook,
    context: WorkbookContext,
    backend: ImageBackend,
    *,
    output_dir: Path,
    reuse_existing: bool = True,
) -> dict[str, Path]:
    """Render each distinct symbol once and return ``{symbol.key: path}``.

    ``reuse_existing`` picks up a drawing already in ``output_dir`` rather than
    regenerating it, which is what makes a shared symbol directory across books
    worth pointing at: the universal symbols get paid for once, ever.
    """
    backend_can_draw_symbols = hasattr(backend, "generate_symbol")
    images: dict[str, Path] = {}
    for symbol in _distinct_symbols(workbook):
        if symbol.key in images:
            continue
        cached = _cached(output_dir, symbol.key) if reuse_existing else None
        if cached is not None:
            logger.info("reusing cached symbol %r from %s", symbol.key, cached)
            images[symbol.key] = cached
            continue
        if not backend_can_draw_symbols:
            logger.warning(
                "backend %r cannot draw symbols; %r left as a placeholder",
                getattr(backend, "name", backend),
                symbol.key,
            )
            continue
        try:
            images[symbol.key] = backend.generate_symbol(symbol, context, output_dir=output_dir)
        except Exception as exc:  # one bad symbol must not cost the whole page
            logger.warning("image generation failed for symbol %r: %s", symbol.key, exc)
    return images


def _distinct_symbols(workbook: Workbook):
    """Every symbol in the book, first occurrence wins, in page order."""
    seen: set[str] = set()
    for page in workbook.pages:
        for symbol in page.symbols:
            if symbol.key not in seen:
                seen.add(symbol.key)
                yield symbol


def _cached(output_dir: Path, key: str) -> Path | None:
    """An existing drawing for ``key``, whatever image extension it was saved as."""
    if not output_dir.is_dir():
        return None
    for path in sorted(output_dir.glob(f"{key}.*")):
        if path.is_file():
            return path
    return None
