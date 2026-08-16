"""Which checked-in drawing a symbol gets, in which variant.

``sources/symbols/`` accumulates artwork across every book ever generated (see
``src/image_backends/sources.py``). It holds the drawings as the image model
returned them, plus two derived variants produced by
``tools/make_shadow_symbols.py``:

``images/<key>.<ext>``
    The original: the subject on white paper with a rule drawn round it.
``cutouts/<key>.png``
    The same drawing with the rule removed, cropped to the ink and cut out onto
    transparency.
``silhouettes/<key>.png``
    That shape filled solid grey — outline *and* enclosed white — so it reads as
    the object's shadow rather than as a faint copy of it.

Both derived variants share a crop box per symbol, so a drawing and its shadow
print at exactly the same size: on a matching page a size difference would be a
free answer.

The lookup is deliberately forgiving. A missing variant is not an error — the
layout prints the same labelled placeholder it prints before any artwork exists
at all — because the derived directories are a cache, not a build output, and a
symbol whose art has not been generated yet must never stop a book from
printing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from src.models.workbook import Workbook

#: Repo root / sources / symbols — the same directory ``sources.py`` writes to.
DEFAULT_SYMBOL_ROOT = Path(__file__).resolve().parents[1] / "sources" / "symbols"

IMAGES = "images"
CUTOUTS = "cutouts"
SILHOUETTES = "silhouettes"
#: Not a drawing variant — the rendered prompt behind ``images/<key>.*``.
#: Only ever written for the library's universal pool (see
#: ``Library.universal_pool()``); a "regional"/"local" symbol has art with
#: no prompt file behind it, typically hand-authored rather than prompted.
PROMPTS = "prompts"


@dataclass(frozen=True)
class SymbolArt:
    """Every variant available for the symbols one book asked for."""

    images: dict[str, Path] = field(default_factory=dict)
    cutouts: dict[str, Path] = field(default_factory=dict)
    silhouettes: dict[str, Path] = field(default_factory=dict)


def symbol_keys(workbook: Workbook) -> tuple[str, ...]:
    """Every distinct symbol key in the book, in page order."""
    keys: list[str] = []
    seen: set[str] = set()
    for page in workbook.pages:
        for symbol in page.symbols:
            if symbol.key not in seen:
                seen.add(symbol.key)
                keys.append(symbol.key)
    return tuple(keys)


def find_variant(
    keys: Iterable[str], variant: str, root: Path | str = DEFAULT_SYMBOL_ROOT
) -> dict[str, Path]:
    """``{key: path}`` for the keys that have a ``<root>/<variant>/<key>.*`` file.

    Matched by extension glob rather than by a fixed ``.png``, the same way
    ``runner._cached`` does it: the image backend saves whatever the model
    returned, and that is not always a PNG.
    """
    directory = Path(root) / variant
    if not directory.is_dir():
        return {}
    found: dict[str, Path] = {}
    for key in keys:
        for path in sorted(directory.glob(f"{key}.*")):
            if path.is_file():
                found[key] = path
                break
    return found


def artwork_for(
    workbook: Workbook,
    *,
    root: Path | str = DEFAULT_SYMBOL_ROOT,
    overrides: dict[str, Path] | None = None,
) -> SymbolArt:
    """Resolve every variant for one book's symbols.

    ``overrides`` is what a caller generated during this run (``--generate-images``
    writes straight into the cache directory and hands the paths back). Those win
    over anything found on disk for the plain drawing; the derived variants are
    only ever produced by the offline tool, so a freshly generated symbol has
    none until that tool is run again — which is the honest answer, not a bug.
    """
    keys = symbol_keys(workbook)
    images = find_variant(keys, IMAGES, root)
    images.update(overrides or {})
    return SymbolArt(
        images=images,
        cutouts=find_variant(keys, CUTOUTS, root),
        silhouettes=find_variant(keys, SILHOUETTES, root),
    )


__all__ = [
    "CUTOUTS",
    "DEFAULT_SYMBOL_ROOT",
    "IMAGES",
    "PROMPTS",
    "SILHOUETTES",
    "SymbolArt",
    "artwork_for",
    "find_variant",
    "symbol_keys",
]
