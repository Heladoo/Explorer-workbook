"""Whether a destination already has a hand-authored doodle/grid sheet.

``sources/Decor/<Name>/`` is where a destination's doodle sheet (the
scattered, multi-object drawing split into individual symbols by
``tools/split_decor.py``) lives once it has been generated and reviewed —
see the symbol-authoring skill. Once a destination has one, ``src/pipeline.py``
should not keep asking for a fresh one on every book: the point of the sheet
is a one-time source for that destination's symbols, not a per-book asset.

Matched by slug rather than exact folder name, so "Pelion" and a folder named
"Pelion" (or "pelion") agree without the caller worrying about case.
"""

from __future__ import annotations

from pathlib import Path

from src.models.context import slugify

DEFAULT_DECOR_ROOT = Path("sources/Decor")

#: Extensions a doodle sheet might have been saved under.
_DOODLE_GLOBS = ("doodle*.png", "doodle*.jpg", "doodle*.jpeg")


def existing_doodle(destination: str, root: Path | str | None = None) -> Path | None:
    """The destination's doodle sheet, if one has already been authored.

    Returns the first match (in the destination's own directory) or ``None``
    if the destination has no directory under ``root`` yet, or has one with
    no file named ``doodle*``.
    """
    decor_root = Path(root) if root is not None else DEFAULT_DECOR_ROOT
    if not decor_root.is_dir():
        return None

    target = slugify(destination)
    for directory in decor_root.iterdir():
        if not directory.is_dir() or slugify(directory.name) != target:
            continue
        for pattern in _DOODLE_GLOBS:
            matches = sorted(directory.glob(pattern))
            if matches:
                return matches[0]
    return None
