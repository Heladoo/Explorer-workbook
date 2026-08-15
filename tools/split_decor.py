"""Split a freeform decor doodle sheet into individual transparent PNGs.

An authoring tool, not part of the generation pipeline: nothing under `src/`
imports it, so the stdlib-only rule for the core generator still holds. It does
need three third-party packages that the pipeline does not:

    python -m pip install pillow numpy scipy

The sheets in `sources/Decor/` are one prompt each and hold ~40 loosely
scattered objects, so there is no grid to crop on. This finds objects by
dilating the ink mask until each drawing's strokes merge into one blob, labels
the connected components, and cuts a tightly trimmed crop per blob.

Blob detection cannot name what it finds. The output is therefore numbered, not
keyed: `crop_007.png` plus a `_contact.png` index sheet and a `manifest.json`,
so the naming pass is a human looking at one picture. Crops are never a drop-in
for `sources/symbols/images/<key>.png` — that cache is keyed off
`UNIVERSAL_SYMBOLS` and needs specific coverage this sheet does not have.

    python tools/split_decor.py "sources/Decor/Pelion/Doodle greece.png"
    python tools/split_decor.py sources/Decor/Pelion/*.png --dry-run
    python tools/split_decor.py sheet.png --merge 8 --min-side 90 -o out/

Nothing is ever deleted: an existing crop file is left alone unless --overwrite.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from scipy import ndimage
except ImportError as exc:  # pragma: no cover - authoring tool
    sys.exit(f"{exc}\n\nThis tool needs: python -m pip install pillow numpy scipy")


# ---------------------------------------------------------------- parameters

INK_LUMA = 200
"""Luma at or below which a pixel counts as ink. The blue domes on the Greece
sheet land near 111, so a single threshold catches coloured accents too."""

ALPHA_WHITE = 250
ALPHA_SOLID = 190
"""Luma ramp for the cut-out alpha: >= ALPHA_WHITE is fully transparent,
<= ALPHA_SOLID fully opaque, antialiased stroke edges in between."""


@dataclass
class Crop:
    index: int
    filename: str
    kind: str
    x: int
    y: int
    width: int
    height: int
    ink_pixels: int
    fill: float


@dataclass
class Blob:
    """One detected object: where it is, and which pixels are actually its own."""

    kind: str
    box: tuple[int, int, int, int]
    ink_pixels: int
    origin: tuple[int, int]
    """Top-left of `mask` in source coordinates."""
    mask: np.ndarray
    """Dilated component footprint — True where this blob owns the pixel."""


# ------------------------------------------------------------------- helpers


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "sheet"


def load_sheet(path: Path) -> tuple[Image.Image, np.ndarray, np.ndarray]:
    """Return (RGBA image, luma array, ink mask)."""
    image = Image.open(path).convert("RGBA")
    rgba = np.asarray(image).astype(np.float32)
    # Composite onto white so transparent regions read as background, not ink.
    alpha = rgba[..., 3:4] / 255.0
    rgb = rgba[..., :3] * alpha + 255.0 * (1.0 - alpha)
    luma = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return image, luma, luma <= INK_LUMA


def maxpool(mask: np.ndarray, k: int) -> np.ndarray:
    """Downscale a boolean mask by `k`, keeping any ink in each block.

    Plain resizing drops hairline strokes; max-pooling never does, which
    matters because component analysis runs on the downscaled copy.
    """
    if k == 1:
        return mask
    h, w = mask.shape
    pad = ((0, -h % k), (0, -w % k))
    padded = np.pad(mask, pad, constant_values=False)
    ph, pw = padded.shape
    return padded.reshape(ph // k, k, pw // k, k).max(axis=(1, 3))


def disk(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    return x * x + y * y <= radius * radius


def tight_bbox(sub: np.ndarray) -> tuple[int, int, int, int] | None:
    """(x0, y0, x1, y1) of the True pixels in `sub`, or None if empty."""
    rows = np.flatnonzero(sub.any(axis=1))
    cols = np.flatnonzero(sub.any(axis=0))
    if rows.size == 0 or cols.size == 0:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1


def cut_out(
    image: Image.Image,
    luma: np.ndarray,
    box: tuple[int, int, int, int],
    own: np.ndarray | None = None,
) -> Image.Image:
    """Crop `box` and replace the white paper with transparency.

    `own` is a boolean mask the size of `box` restricting the crop to one blob's
    own footprint. Objects on these sheets are scattered at angles, so a
    diagonal drawing's bounding rectangle routinely covers two or three
    neighbours; without this the ouzo bottle arrives with a church and a bunch
    of grapes attached.
    """
    x0, y0, x1, y1 = box
    crop = np.asarray(image.crop(box)).astype(np.float32)
    window = luma[y0:y1, x0:x1]
    ramp = (ALPHA_WHITE - window) * (255.0 / (ALPHA_WHITE - ALPHA_SOLID))
    alpha = np.clip(ramp, 0.0, 255.0)
    if own is not None:
        alpha *= own
    # Never resurrect pixels the source had already made transparent.
    crop[..., 3] = np.minimum(alpha, crop[..., 3])
    return Image.fromarray(crop.round().astype(np.uint8), mode="RGBA")


def pad_square(image: Image.Image) -> Image.Image:
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


# --------------------------------------------------------------- the splitter


def find_crops(
    luma: np.ndarray,
    ink: np.ndarray,
    *,
    scale: int,
    merge: int,
    min_side: int,
    min_ink: int,
    band_aspect: float,
    band_height: float,
) -> list[Blob]:
    """Find every object on the sheet.

    `kind` is "symbol" for a normal drawing and "band" for the long thin runs —
    meander borders and rows of lettering — which want culling or cropping by
    hand rather than mixing into the symbol pile.
    """
    small = maxpool(ink, scale)
    merged = ndimage.binary_dilation(small, structure=disk(merge))
    labels, _ = ndimage.label(merged)

    sheet_height = luma.shape[0]
    found: list[Blob] = []

    for index, window in enumerate(ndimage.find_objects(labels), start=1):
        if window is None:
            continue
        ys, xs = window
        # Isolate this component so a neighbour bleeding into the same
        # rectangle cannot stop the bbox from shrinking onto its own strokes.
        component = np.repeat(
            np.repeat(labels[ys, xs] == index, scale, axis=0), scale, axis=1
        )
        y0, x0 = ys.start * scale, xs.start * scale
        region = ink[y0 : y0 + component.shape[0], x0 : x0 + component.shape[1]]
        component = component[: region.shape[0], : region.shape[1]]
        own = region & component

        bbox = tight_bbox(own)
        if bbox is None:
            continue
        bx0, by0, bx1, by1 = bbox
        box = (x0 + bx0, y0 + by0, x0 + bx1, y0 + by1)
        width, height = box[2] - box[0], box[3] - box[1]
        pixels = int(own.sum())

        if pixels < min_ink or max(width, height) < min_side:
            continue

        aspect = max(width / height, height / width)
        thin = min(width, height) < band_height * sheet_height
        kind = "band" if aspect >= band_aspect and thin else "symbol"
        found.append(Blob(kind, box, pixels, (x0, y0), component))

    # Reading order, so crop numbers roughly track how you scan the sheet.
    found.sort(key=lambda blob: (blob.box[1] // 200, blob.box[0]))
    return found


def contact_sheet(crops: list[tuple[Crop, Image.Image]], columns: int = 8) -> Image.Image:
    """An index sheet of every crop with its number, for the naming pass."""
    cell, label = 220, 26
    rows = max(1, -(-len(crops) // columns))
    sheet = Image.new("RGB", (columns * cell, rows * (cell + label)), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=18)
    except TypeError:  # pragma: no cover - older Pillow
        font = ImageFont.load_default()

    for position, (meta, image) in enumerate(crops):
        cx = (position % columns) * cell
        cy = (position // columns) * (cell + label)
        thumb = image.copy()
        thumb.thumbnail((cell - 16, cell - 16))
        backdrop = Image.new("RGB", thumb.size, "white")
        backdrop.paste(thumb, mask=thumb.split()[3])
        sheet.paste(
            backdrop,
            (cx + (cell - thumb.width) // 2, cy + (cell - thumb.height) // 2),
        )
        caption = f"{meta.index:03d}  {meta.kind[0]}  {meta.width}x{meta.height}"
        draw.text((cx + 8, cy + cell + 4), caption, fill="black", font=font)
        draw.rectangle([cx, cy, cx + cell - 1, cy + cell + label - 1], outline="#cccccc")
    return sheet


def split(path: Path, out_root: Path | None, args: argparse.Namespace) -> int:
    image, luma, ink = load_sheet(path)
    found = find_crops(
        luma,
        ink,
        scale=args.scale,
        merge=args.merge,
        min_side=args.min_side,
        min_ink=args.min_ink,
        band_aspect=args.band_aspect,
        band_height=args.band_height,
    )

    symbols = sum(1 for blob in found if blob.kind == "symbol")
    print(f"\n{path.name}: {symbols} symbols, {len(found) - symbols} bands")
    if args.dry_run:
        for number, blob in enumerate(found, start=1):
            x0, y0, x1, y1 = blob.box
            print(f"  {number:03d}  {blob.kind:6s}  {x1 - x0:4d}x{y1 - y0:<4d}  ink={blob.ink_pixels}")
        return 0

    out_dir = (out_root or path.parent / "split") / slugify(path.stem)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[Crop] = []
    thumbs: list[tuple[Crop, Image.Image]] = []
    skipped = 0

    for number, blob in enumerate(found, start=1):
        pad = args.pad
        box = (
            max(0, blob.box[0] - pad),
            max(0, blob.box[1] - pad),
            min(luma.shape[1], blob.box[2] + pad),
            min(luma.shape[0], blob.box[3] + pad),
        )
        own = None
        if args.isolate:
            # Re-window the blob's footprint onto the padded crop rectangle.
            ox, oy = blob.origin
            own = np.zeros(luma.shape, dtype=bool)
            own[oy : oy + blob.mask.shape[0], ox : ox + blob.mask.shape[1]] = blob.mask
            own = own[box[1] : box[3], box[0] : box[2]]
        crop = cut_out(image, luma, box, own)
        if args.square:
            crop = pad_square(crop)

        width, height = blob.box[2] - blob.box[0], blob.box[3] - blob.box[1]
        name = f"{blob.kind}_{number:03d}.png"
        meta = Crop(
            index=number,
            filename=name,
            kind=blob.kind,
            x=blob.box[0],
            y=blob.box[1],
            width=width,
            height=height,
            ink_pixels=blob.ink_pixels,
            fill=round(blob.ink_pixels / max(1, width * height), 4),
        )
        manifest.append(meta)
        thumbs.append((meta, crop))

        target = out_dir / name
        if target.exists() and not args.overwrite:
            skipped += 1
            continue
        crop.save(target)

    (out_dir / "manifest.json").write_text(
        json.dumps(
            {"source": path.name, "size": list(image.size), "crops": [asdict(c) for c in manifest]},
            indent=2,
        ),
        encoding="utf-8",
    )
    contact_sheet(thumbs).save(out_dir / "_contact.png")

    print(f"  wrote {len(manifest) - skipped} crops to {out_dir}")
    if skipped:
        print(f"  left {skipped} existing files alone (pass --overwrite to replace)")
    print(f"  review {out_dir / '_contact.png'}, then rename the keepers")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("images", nargs="+", type=Path, help="decor sheet PNG(s)")
    parser.add_argument("-o", "--out", type=Path, help="output root (default: <sheet dir>/split)")
    parser.add_argument("--dry-run", action="store_true", help="list what would be cut, write nothing")
    parser.add_argument("--overwrite", action="store_true", help="replace crops that already exist")
    parser.add_argument("--square", action="store_true", help="pad each crop to a square canvas")
    parser.add_argument(
        "--isolate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="erase neighbouring drawings that fall inside a crop's rectangle (default: on)",
    )
    parser.add_argument("--scale", type=int, default=4, help="analysis downscale factor (default 4)")
    parser.add_argument(
        "--merge",
        type=int,
        default=2,
        help="dilation radius in analysis pixels (default 2 = 8 source px). "
        "Raise it if one drawing splits into pieces, lower it if neighbours fuse. "
        "The usable band is narrow: on the Pelion sheets 3 already fuses the page.",
    )
    parser.add_argument("--pad", type=int, default=12, help="whitespace kept around each crop")
    parser.add_argument("--min-side", type=int, default=70, help="drop crops smaller than this")
    parser.add_argument("--min-ink", type=int, default=900, help="drop crops with less ink than this")
    parser.add_argument("--band-aspect", type=float, default=4.0, help="aspect ratio that marks a band")
    parser.add_argument("--band-height", type=float, default=0.09, help="band thinness, as a fraction of sheet height")
    args = parser.parse_args(argv)

    for path in args.images:
        if not path.is_file():
            print(f"skipping missing file: {path}", file=sys.stderr)
            continue
        split(path, args.out, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
