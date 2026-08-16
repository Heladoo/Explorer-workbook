"""Derive shadow-matching artwork from the checked-in symbol drawings.

An authoring tool, not part of the generation pipeline: nothing under `src/`
imports it, so the stdlib-only rule for the core generator still holds. It
needs the same three packages `split_decor.py` does:

    python -m pip install pillow numpy scipy

Every drawing in `sources/symbols/images/` arrives as a 1254px square of white
paper with a thin black rectangle ruled around it. Neither the paper nor the
rule belongs on a matching page — two columns of framed white squares read as a
table, not as a pair of shapes — so this pass produces the two variants the
`matching` layout actually places, both cut to the *same* crop box so a picture
and its shadow print at identical size:

`sources/symbols/cutouts/<key>.png`
    The drawing alone: frame removed, cropped to the ink, white paper replaced
    with transparency, stroke edges kept antialiased.
`sources/symbols/silhouettes/<key>.png`
    The same shape filled solid mid-grey — outline *and* the white it encloses,
    so the interior detail a child would otherwise match on is gone. This is
    the whole reason the fill happens here rather than in CSS: a filter can
    only recolour ink that already exists, and the silhouette of a bicycle is
    mostly pixels the source drawing left white.

    A closed loop (a wheel, a lens) fills on its own. Several drawings are
    not closed loops at all — a mountain range, a tractor, a train — because
    the artist never drew a baseline for them to rest on, so their own
    interior leaks out to the true background through that missing edge
    before it can be recognised as a hole. `_ground_curtain` closes that one
    specific, common gap (see its docstring for why only the bottom edge is
    trusted by default) and `_close_gaps` bridges a stroke that stops just
    short of a neighbour it should touch (a tractor's fender line, short of
    its wheel rim).

Both are transparent PNGs, so the print layout composites them on the page
background and the ink-saver palette still applies.

    python tools/make_shadow_symbols.py                    # derive everything missing
    python tools/make_shadow_symbols.py --dry-run          # report, write nothing
    python tools/make_shadow_symbols.py bicycle dog        # just these keys
    python tools/make_shadow_symbols.py --overwrite --grey 140

Nothing is ever deleted, and an existing derivative is left alone unless
`--overwrite` is passed. A `_contact.png` index sheet lands in each output
directory so the whole set can be eyeballed in one look — the frame detection
below is heuristic, and a symbol whose drawing touches its own frame is exactly
the kind of thing only a human notices.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from scipy import ndimage
except ImportError as exc:  # pragma: no cover - authoring tool
    sys.exit(f"{exc}\n\nThis tool needs: python -m pip install pillow numpy scipy")


# ---------------------------------------------------------------- parameters

SOURCE_DIR = Path("sources/symbols/images")
CUTOUT_DIR = Path("sources/symbols/cutouts")
SILHOUETTE_DIR = Path("sources/symbols/silhouettes")

INK_LUMA = 200
"""Luma at or below which a pixel counts as ink — same threshold as
`split_decor.py`, so coloured accents count as ink too."""

ALPHA_WHITE = 250
ALPHA_SOLID = 190
"""Luma ramp for the cut-out alpha: >= ALPHA_WHITE is fully transparent,
<= ALPHA_SOLID fully opaque, antialiased stroke edges in between."""

FRAME_SPAN = 0.7
"""A component whose bounding box covers at least this fraction of *both* the
canvas width and height is a candidate for the ruled border. The rules are not
drawn to a consistent inset across the set — some sit 30px from the edge and
some 157px — so this is deliberately loose, and the perimeter test below is
what actually decides."""

FRAME_PERIMETER = 0.9
"""...and it is the border only if at least this fraction of its pixels lie in
a thin band around its own bounding box. That is what a ruled rectangle *is*,
and no drawing satisfies it: a bicycle spanning the same box puts most of its
ink through the middle."""

FRAME_BAND = 0.03
"""Width of that band, as a fraction of the bounding box's shorter side. The
rules measure ~12px on a 1254px sheet, so this leaves room to spare without
being wide enough for a drawing to hide in."""

SLIVER_WIDTH = 0.02
SLIVER_LENGTH = 0.5
"""An edge-hugging run thinner than SLIVER_WIDTH of the sheet and longer than
SLIVER_LENGTH of it is leftover border, not drawing — see `_edge_slivers`."""

SHADOW_GREY = 120
"""Mid-grey fill for the silhouette. Dark enough to read as a shadow at grid
size, light enough not to flood a home printer with ink."""

PAD = 8
"""Whitespace kept around the cropped ink, in source pixels."""

GROUND_SIDES: dict[str, tuple[str, ...]] = {
    # A drawing whose interior never closes along the bottom because there is
    # nothing to draw a baseline against — a mountain range, a tractor and a
    # train both end mid-air, with no ink at all closing off what is "inside"
    # from the true background beneath. `_ground_curtain` treats that edge as
    # a surface the subject rests on, closing exactly that gap.
    #
    # This is a per-key allow-list, not a rule applied to every symbol,
    # because "closed off by *some* edge" is not true in general: a bridge's
    # arches are legitimately open underneath (that's the river), and running
    # this over every symbol once turned that open water into a solid grey
    # rectangle. Trusting a *side* edge is an even narrower claim — that the
    # drawing was cropped there, not merely resting on something — so it is
    # even less safe to assume by default. Add a key here only after
    # checking its `_contact.png` silhouette by eye.
    "mountain": ("bottom",),
    "tractor": ("bottom",),
    "train": ("bottom",),
}

FORCE_STRIP_FRAME: set[str] = {
    # `strip_frame`'s ">60% of the ink" guard assumes that much frame usually
    # means the frame merged with the drawing into one component — a false
    # merge is unsafe to strip blindly. `water-bottle`'s frame and drawing are
    # in fact two separate connected components (checked by hand: the frame
    # alone is 63% of the total ink here purely because the bottle's own
    # linework is thin, not because anything touches), so stripping it is
    # safe. Add a key here only after confirming that separation yourself —
    # this bypasses the one safety net that would otherwise catch a real
    # merge.
    "water-bottle",
}

EXTRA_CLOSE_RADIUS: dict[str, int] = {
    # The tractor's front mudguard line ends a few pixels short of the wheel
    # rim it curves down to meet, leaving a thin crescent of true interior
    # that reads as background. A closing radius here bridges exactly that:
    # see `_close_gaps` for why a *per-symbol* radius, not a global one — the
    # same closing tried at this radius across the whole bank welded shut
    # bicycle spokes, sunglasses lenses and the stop sign's own octagon, all
    # of which have detail finer than this specific gap. Add a key here only
    # after checking its `_contact.png` silhouette by eye.
    "tractor": 12,
}

MAX_SIDE = 600
"""Longest edge of a written derivative. The source is 1254px square; a symbol
prints about 30mm wide, so past this the file is carrying detail no printer
will ever resolve."""


@dataclass
class Derived:
    key: str
    cutout: Image.Image
    silhouette: Image.Image
    #: Crop box in source coordinates, and how much ink the frame removal took.
    box: tuple[int, int, int, int]
    frame_pixels: int
    ink_pixels: int
    note: str = ""


# ------------------------------------------------------------------- helpers


def load(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (luma, ink mask) for a symbol drawing, composited onto white."""
    rgba = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)
    alpha = rgba[..., 3:4] / 255.0
    rgb = rgba[..., :3] * alpha + 255.0 * (1.0 - alpha)
    luma = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return luma, luma <= INK_LUMA


def strip_frame(ink: np.ndarray, key: str | None = None) -> tuple[np.ndarray, int, str]:
    """Erase the ruled border, returning (ink without it, pixels removed, note).

    The border is found by shape rather than by position: label the ink, and
    drop any component that spans most of the canvas *and* keeps nearly all of
    its pixels in a thin band around its own bounding box. Position is no use
    here — the rules on these sheets are inset anywhere from 30px to 157px, and
    a couple are not even centred — but "hollow rectangle" describes every one
    of them and none of the drawings.

    A drawing whose strokes touch the border merges into one component with it:
    the merged shape fails the perimeter test, so nothing is removed and the
    caller is told. That is the safe failure — the sheet prints as it always
    did — and the `note` shows up in the run report and on the contact sheet,
    because the silhouette of an un-stripped sheet is a solid grey rectangle
    and it needs a human to look at it.
    """
    height, width = ink.shape
    labels, count = ndimage.label(ink, structure=np.ones((3, 3), dtype=bool))
    if count == 0:
        return ink, 0, "no ink found"

    total = int(ink.sum())
    frame = np.zeros_like(ink)

    for index, window in enumerate(ndimage.find_objects(labels), start=1):
        ys, xs = window
        box_height, box_width = ys.stop - ys.start, xs.stop - xs.start
        if box_height < FRAME_SPAN * height or box_width < FRAME_SPAN * width:
            continue
        component = labels[ys, xs] == index
        band = max(4, round(FRAME_BAND * min(box_height, box_width)))
        interior = np.zeros_like(component)
        interior[band:-band, band:-band] = component[band:-band, band:-band]
        on_perimeter = 1.0 - interior.sum() / max(1, component.sum())
        if on_perimeter >= FRAME_PERIMETER:
            frame |= labels == index

    frame |= _edge_slivers(labels, count, ink.shape)

    removed = int(frame.sum())
    if removed == 0:
        return ink, 0, "no frame detected"
    if removed > 0.6 * total and key not in FORCE_STRIP_FRAME:
        return ink, 0, "frame merges with the drawing — left in place"
    return ink & ~frame, removed, ""


def _edge_slivers(labels: np.ndarray, count: int, shape: tuple[int, int]) -> np.ndarray:
    """Ink hugging the canvas rim as a hairline — the rest of a clipped border.

    `ice-cream.png` carries a 6px strip of a second rule running down its right
    edge. It is not a rectangle so the perimeter test never sees it, but left
    in it drags the crop box out to the full sheet width and hangs a stray line
    beside the cone. A run of ink long enough to cross the sheet and only a few
    pixels wide, flush against an edge, is never part of a drawing.
    """
    height, width = shape
    slivers = np.zeros(shape, dtype=bool)
    for index, window in enumerate(ndimage.find_objects(labels), start=1):
        ys, xs = window
        box_height, box_width = ys.stop - ys.start, xs.stop - xs.start
        touches = ys.start == 0 or xs.start == 0 or ys.stop == height or xs.stop == width
        hairline = min(box_height, box_width) <= SLIVER_WIDTH * min(height, width)
        long_run = max(box_height / height, box_width / width) >= SLIVER_LENGTH
        if touches and hairline and long_run:
            slivers |= labels == index
    return slivers


def tight_box(ink: np.ndarray, pad: int) -> tuple[int, int, int, int] | None:
    rows = np.flatnonzero(ink.any(axis=1))
    cols = np.flatnonzero(ink.any(axis=0))
    if rows.size == 0 or cols.size == 0:
        return None
    height, width = ink.shape
    return (
        max(0, int(cols[0]) - pad),
        max(0, int(rows[0]) - pad),
        min(width, int(cols[-1]) + 1 + pad),
        min(height, int(rows[-1]) + 1 + pad),
    )


def stroke_alpha(luma: np.ndarray) -> np.ndarray:
    """Antialiased alpha from the paper: white is transparent, ink is solid."""
    ramp = (ALPHA_WHITE - luma) * (255.0 / (ALPHA_WHITE - ALPHA_SOLID))
    return np.clip(ramp, 0.0, 255.0)


def to_rgba(alpha: np.ndarray, value: int) -> Image.Image:
    rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    rgba[..., :3] = value
    rgba[..., 3] = alpha.round().astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def _disk(radius: int) -> np.ndarray:
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    return x * x + y * y <= radius * radius


def _close_gaps(ink: np.ndarray, radius: int) -> np.ndarray:
    """Bridge a stroke that stops just short of a neighbouring one.

    Closing can only ever bridge a *narrow* gap — it dilates outward by
    `radius` on both sides of a gap and then erodes back, so two strokes more
    than `2 * radius` apart are untouched. That is exactly the distinction
    this needs: the crescent of background between a tractor's fender line
    and its wheel rim is a few pixels wide and closes at this radius; a
    bicycle's open front triangle is hundreds of pixels across and does not.
    Monotonic in the same direction as everything else here — closing only
    ever adds ink, never removes it, so it can't un-enclose a hole that
    `binary_fill_holes` already finds on its own.
    """
    return ndimage.binary_closing(ink, structure=_disk(radius))


def _ground_curtain(ink: np.ndarray, side: str) -> np.ndarray:
    """Extend every stroke that reaches toward `side` on out to the edge.

    Several of these drawings (a mountain range, a tractor's wheels, a
    train's undercarriage) never close their own outline along the bottom —
    the strokes simply stop, because there is nothing to draw a baseline
    against. `binary_fill_holes` alone leaves the whole interior above a stop
    like that unfilled: the true background reaches it by flowing underneath,
    through the gap where a baseline would be. Extending every column's own
    lowest ink pixel down to the crop edge closes exactly that gap and
    nothing else — a real opening *within* the silhouette (the sky between
    two separate mountain peaks) still has ink below it in that same column,
    so this never touches it.

    Called per key, per side, from `GROUND_SIDES` — never on every symbol,
    because not every open edge is this kind of gap (a bridge's arches are
    legitimately open underneath, onto the river).
    """
    h, w = ink.shape
    curtained = ink.copy()
    if side in ("bottom", "top"):
        has_ink = ink.any(axis=0)
        if side == "bottom":
            edge = np.where(has_ink, h - 1 - np.argmax(ink[::-1, :], axis=0), -1)
            for x in np.flatnonzero(has_ink):
                curtained[edge[x] :, x] = True
        else:
            edge = np.where(has_ink, np.argmax(ink, axis=0), -1)
            for x in np.flatnonzero(has_ink):
                curtained[: edge[x] + 1, x] = True
    else:
        has_ink = ink.any(axis=1)
        if side == "right":
            edge = np.where(has_ink, w - 1 - np.argmax(ink[:, ::-1], axis=1), -1)
            for y in np.flatnonzero(has_ink):
                curtained[y, edge[y] :] = True
        else:
            edge = np.where(has_ink, np.argmax(ink, axis=1), -1)
            for y in np.flatnonzero(has_ink):
                curtained[y, : edge[y] + 1] = True
    return curtained


def fit(image: Image.Image, max_side: int) -> Image.Image:
    if max_side <= 0 or max(image.size) <= max_side:
        return image
    scale = max_side / max(image.size)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    return image.resize(size, Image.LANCZOS)


# ---------------------------------------------------------------- the derivation


def derive(path: Path, *, pad: int, grey: int, max_side: int) -> Derived | None:
    luma, ink = load(path)
    ink, frame_pixels, note = strip_frame(ink, key=path.stem)

    box = tight_box(ink, pad)
    if box is None:
        print(f"  {path.name}: no drawing left after frame removal — skipped")
        return None

    x0, y0, x1, y1 = box
    window_luma = luma[y0:y1, x0:x1]
    window_ink = ink[y0:y1, x0:x1]

    # The frame is gone from the mask but still sits in `luma`, so build the
    # cut-out's alpha from the ramp and then mute anything the mask disowns.
    # Dilating the mask first keeps the antialiased skirt around every stroke,
    # which is the difference between a clean edge and a jagged one.
    kept = ndimage.binary_dilation(window_ink, structure=np.ones((5, 5), dtype=bool))
    cutout_alpha = stroke_alpha(window_luma) * kept

    # The silhouette is the shape *plus everything it encloses* — a wheel's
    # spokes, a window, the hollow of a handle. Anything still open to the
    # outside (the gap between a bicycle's wheels) is not enclosed and stays
    # transparent, which is what makes the result read as a cast shadow rather
    # than a blob. `_close_gaps` and `_ground_curtain` only ever add ink before
    # this runs, so a hole this alone would already find is untouched by them.
    for_fill = window_ink
    close_radius = EXTRA_CLOSE_RADIUS.get(path.stem, 0)
    if close_radius:
        for_fill = _close_gaps(for_fill, close_radius)
    for side in GROUND_SIDES.get(path.stem, ()):
        for_fill = _ground_curtain(for_fill, side)
    filled = ndimage.binary_fill_holes(for_fill)
    silhouette_alpha = np.where(filled, 255.0, cutout_alpha)

    return Derived(
        key=path.stem,
        cutout=fit(to_rgba(cutout_alpha, 0), max_side),
        silhouette=fit(to_rgba(silhouette_alpha, grey), max_side),
        box=box,
        frame_pixels=frame_pixels,
        ink_pixels=int(window_ink.sum()),
        note=note,
    )


def contact_sheet(items: list[Derived], attribute: str, columns: int = 6) -> Image.Image:
    """An index sheet of one variant, for the eyeball pass."""
    cell, label = 200, 24
    rows = max(1, -(-len(items) // columns))
    sheet = Image.new("RGB", (columns * cell, rows * (cell + label)), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=15)
    except TypeError:  # pragma: no cover - older Pillow
        font = ImageFont.load_default()

    for position, item in enumerate(items):
        cx = (position % columns) * cell
        cy = (position // columns) * (cell + label)
        thumb = getattr(item, attribute).copy()
        thumb.thumbnail((cell - 16, cell - 16))
        backdrop = Image.new("RGB", thumb.size, "white")
        backdrop.paste(thumb, mask=thumb.split()[3])
        sheet.paste(
            backdrop, (cx + (cell - thumb.width) // 2, cy + (cell - thumb.height) // 2)
        )
        caption = item.key if not item.note else f"{item.key} !"
        draw.text((cx + 6, cy + cell + 4), caption[:26], fill="black", font=font)
        draw.rectangle([cx, cy, cx + cell - 1, cy + cell + label - 1], outline="#cccccc")
    return sheet


def run(args: argparse.Namespace) -> int:
    source_dir: Path = args.source
    if not source_dir.is_dir():
        print(f"no such directory: {source_dir}", file=sys.stderr)
        return 1

    paths = sorted(source_dir.glob("*.png"))
    if args.keys:
        wanted = set(args.keys)
        paths = [path for path in paths if path.stem in wanted]
        missing = wanted - {path.stem for path in paths}
        for key in sorted(missing):
            print(f"no source drawing for {key!r} in {source_dir}", file=sys.stderr)

    print(f"{len(paths)} drawing(s) in {source_dir}")
    derived: list[Derived] = []
    for path in paths:
        item = derive(path, pad=args.pad, grey=args.grey, max_side=args.max_side)
        if item is None:
            continue
        derived.append(item)
        x0, y0, x1, y1 = item.box
        flag = f"  <- {item.note}" if item.note else ""
        print(
            f"  {item.key:22s} crop {x1 - x0:4d}x{y1 - y0:<4d}  "
            f"frame {item.frame_pixels:6d}px  ink {item.ink_pixels:6d}px{flag}"
        )

    if args.dry_run:
        print("\ndry run — nothing written")
        return 0

    written = skipped = 0
    for directory, attribute in ((args.cutouts, "cutout"), (args.silhouettes, "silhouette")):
        directory.mkdir(parents=True, exist_ok=True)
        for item in derived:
            target = directory / f"{item.key}.png"
            if target.exists() and not args.overwrite:
                skipped += 1
                continue
            getattr(item, attribute).save(target)
            written += 1
        if derived:
            contact_sheet(derived, attribute).save(directory / "_contact.png")

    print(f"\nwrote {written} file(s) to {args.cutouts} and {args.silhouettes}")
    if skipped:
        print(f"left {skipped} existing file(s) alone (pass --overwrite to replace)")
    flagged = [item.key for item in derived if item.note]
    if flagged:
        print(f"check by hand ({len(flagged)}): {', '.join(flagged)}")
    print(f"review {args.cutouts / '_contact.png'} and {args.silhouettes / '_contact.png'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("keys", nargs="*", help="symbol keys to derive (default: all)")
    parser.add_argument("--source", type=Path, default=SOURCE_DIR, help="source drawings")
    parser.add_argument("--cutouts", type=Path, default=CUTOUT_DIR, help="cut-out output dir")
    parser.add_argument(
        "--silhouettes", type=Path, default=SILHOUETTE_DIR, help="silhouette output dir"
    )
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    parser.add_argument("--overwrite", action="store_true", help="replace existing derivatives")
    parser.add_argument("--pad", type=int, default=PAD, help=f"crop padding (default {PAD})")
    parser.add_argument(
        "--grey", type=int, default=SHADOW_GREY, help=f"silhouette grey 0-255 (default {SHADOW_GREY})"
    )
    parser.add_argument(
        "--max-side", type=int, default=MAX_SIDE, help=f"longest edge written (default {MAX_SIDE})"
    )
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
