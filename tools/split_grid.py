"""Split an evenly-spaced grid sheet (each cell already ruled with its own
border) into individual per-symbol PNGs, in reading order.

An authoring tool, not part of the generation pipeline — same stdlib-only
rule as `split_decor.py` and `make_shadow_symbols.py`:

    python -m pip install pillow numpy scipy

Unlike `split_decor.py` (built for a freeform doodle sheet with ~40 loosely
scattered objects and no grid to crop on), this is for sheets like
`sources/symbols/Grid/*.png`: a regular grid of individually-bordered cells,
possibly split across more than one block (a 6x2 block, a gap, then a 4x2
block). Blob-merge splitting fuses a sheet like this into whole rows, because
each cell's own frame nearly touches its neighbours' — this tool instead
finds the blank rows/columns *between* cells and cuts exactly there.

A cell painted solid red is a "skip this one" marker some sheets use for a
placeholder/reserved slot; it is detected and skipped automatically (pass
`--no-skip-red` to keep it, `--red-key <key>` to name what red pixels look
like if a sheet uses a different marker colour).

    python tools/split_grid.py "sources/symbols/Grid/grid animals.png" --dry-run
    python tools/split_grid.py "sources/symbols/Grid/grid animals.png" \\
        --labels "owl,dolphins,brown-bear,swallows-nesting,goat,kestrel, \\
                  squirrel,swan,fox,monkey,camel, \\
                  horse,cow,nubian-ibex,seal, \\
                  eagle,turtle,donkey"

`--labels` are matched to cells in reading order (row-major, skipped cells
consumed silently) and slugified into `<key>.png`. Omit `--labels` to get
numbered `cell_NNN.png` crops plus a `_contact.png` and `manifest.json`, the
same review-then-rename workflow `split_decor.py` uses.

Nothing is ever deleted; an existing output file is left alone unless
`--overwrite`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - authoring tool
    sys.exit(f"{exc}\n\nThis tool needs: python -m pip install pillow numpy scipy")


INK_LUMA = 200
"""Same threshold `split_decor.py`/`make_shadow_symbols.py` use."""

RED_MIN_FRACTION = 0.08
"""A cell is "red-marked" if at least this fraction of its pixels are red."""


@dataclass
class Cell:
    index: int
    row: int
    col: int
    box: tuple[int, int, int, int]
    skipped: bool


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "cell"


def load(path: Path) -> tuple[Image.Image, np.ndarray, np.ndarray]:
    image = Image.open(path).convert("RGBA")
    rgba = np.asarray(image).astype(np.float32)
    alpha = rgba[..., 3:4] / 255.0
    rgb = rgba[..., :3] * alpha + 255.0 * (1.0 - alpha)
    luma = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return image, rgba, luma


def _runs(is_ink: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous [start, end) index ranges where `is_ink` is True."""
    runs = []
    start = None
    for i, v in enumerate(is_ink.tolist() + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i))
            start = None
    return runs


def find_row_bands(luma: np.ndarray) -> list[tuple[int, int]]:
    ink = luma <= INK_LUMA
    has_ink = ink.any(axis=1)
    return _runs(has_ink)


def find_col_bands(luma: np.ndarray, y0: int, y1: int) -> list[tuple[int, int]]:
    ink = luma[y0:y1, :] <= INK_LUMA
    has_ink = ink.any(axis=0)
    return _runs(has_ink)


def is_red_marked(rgba: np.ndarray, box: tuple[int, int, int, int]) -> bool:
    x0, y0, x1, y1 = box
    region = rgba[y0:y1, x0:x1]
    r, g, b, a = region[..., 0], region[..., 1], region[..., 2], region[..., 3]
    red = (r > 170) & (g < 110) & (b < 110) & (a > 40)
    return bool(red.mean() > RED_MIN_FRACTION)


def find_cells(image: Image.Image, rgba: np.ndarray, luma: np.ndarray, pad: int) -> list[Cell]:
    cells: list[Cell] = []
    index = 0
    for row, (y0, y1) in enumerate(find_row_bands(luma)):
        for col, (x0, x1) in enumerate(find_col_bands(luma, y0, y1)):
            box = (
                max(0, x0 - pad),
                max(0, y0 - pad),
                min(image.width, x1 + pad),
                min(image.height, y1 + pad),
            )
            index += 1
            cells.append(Cell(index, row, col, box, skipped=is_red_marked(rgba, box)))
    return cells


def contact_sheet(cells: list[Cell], image: Image.Image, names: list[str], columns: int = 6) -> Image.Image:
    cell_size, label_h = 220, 26
    rows = max(1, -(-len(cells) // columns))
    sheet = Image.new("RGB", (columns * cell_size, rows * (cell_size + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=16)
    except TypeError:  # pragma: no cover - older Pillow
        font = ImageFont.load_default()

    for position, (cell, name) in enumerate(zip(cells, names)):
        cx = (position % columns) * cell_size
        cy = (position // columns) * (cell_size + label_h)
        thumb = image.crop(cell.box).convert("RGBA")
        thumb.thumbnail((cell_size - 16, cell_size - 16))
        backdrop = Image.new("RGB", thumb.size, "white")
        backdrop.paste(thumb, mask=thumb.split()[3])
        sheet.paste(backdrop, (cx + (cell_size - thumb.width) // 2, cy + (cell_size - thumb.height) // 2))
        caption = f"{cell.index:03d} {name}"
        draw.text((cx + 6, cy + cell_size + 4), caption[:26], fill="black", font=font)
        draw.rectangle([cx, cy, cx + cell_size - 1, cy + cell_size + label_h - 1], outline="#cccccc")
    return sheet


def run(args: argparse.Namespace) -> int:
    path: Path = args.image
    image, rgba, luma = load(path)
    cells = find_cells(image, rgba, luma, pad=args.pad)
    if not args.skip_red:
        for cell in cells:
            cell.skipped = False

    kept = [c for c in cells if not c.skipped]
    skipped = [c for c in cells if c.skipped]
    print(f"{path.name}: {len(cells)} cell(s) found, {len(skipped)} skipped (red-marked)")

    labels: list[str] | None = None
    if args.labels:
        labels = [part.strip() for part in args.labels.split(",") if part.strip()]
        if len(labels) != len(kept):
            print(
                f"error: {len(labels)} label(s) given but {len(kept)} non-skipped cell(s) "
                f"found — check --labels against the dry-run listing below.",
                file=sys.stderr,
            )
            args.dry_run = True

    names = []
    li = 0
    for cell in cells:
        if cell.skipped:
            names.append("(skipped)")
            continue
        if labels:
            names.append(slugify(labels[li]))
            li += 1
        else:
            names.append(f"cell_{cell.index:03d}")

    for cell, name in zip(cells, names):
        x0, y0, x1, y1 = cell.box
        flag = "  <- SKIPPED (red)" if cell.skipped else ""
        print(f"  {cell.index:03d}  row {cell.row} col {cell.col}  {x1-x0}x{y1-y0}  -> {name}{flag}")

    if args.dry_run:
        print("\ndry run — nothing written")
        return 0

    out_dir = args.out or (path.parent / "split" / slugify(path.stem))
    out_dir.mkdir(parents=True, exist_ok=True)

    written = existed = 0
    manifest = []
    for cell, name in zip(cells, names):
        manifest.append({**asdict(cell), "name": name})
        if cell.skipped:
            continue
        target = out_dir / f"{name}.png"
        if target.exists() and not args.overwrite:
            existed += 1
            continue
        image.crop(cell.box).save(target)
        written += 1

    (out_dir / "manifest.json").write_text(
        json.dumps({"source": path.name, "size": list(image.size), "cells": manifest}, indent=2),
        encoding="utf-8",
    )
    contact_sheet(cells, image, names).save(out_dir / "_contact.png")

    print(f"\nwrote {written} file(s) to {out_dir}")
    if existed:
        print(f"left {existed} existing file(s) alone (pass --overwrite to replace)")
    print(f"review {out_dir / '_contact.png'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("image", type=Path, help="grid sheet PNG")
    parser.add_argument("-o", "--out", type=Path, help="output dir (default: <sheet dir>/split/<slug>)")
    parser.add_argument("--labels", help="comma-separated names for non-skipped cells, in reading order")
    parser.add_argument("--dry-run", action="store_true", help="list what would be cut, write nothing")
    parser.add_argument("--overwrite", action="store_true", help="replace files that already exist")
    parser.add_argument("--pad", type=int, default=4, help="whitespace kept around each detected cell (default 4)")
    parser.add_argument(
        "--skip-red",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="auto-skip cells that are mostly painted solid red (default: on)",
    )
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
