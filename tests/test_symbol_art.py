"""The checked-in symbol cache, and which variant a page gets."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.activities._symbols import UNIVERSAL_SYMBOLS
from src.activities.matching import _SHADOW_UNSUITABLE
from src.symbol_art import (
    CUTOUTS,
    DEFAULT_SYMBOL_ROOT,
    IMAGES,
    SILHOUETTES,
    artwork_for,
    find_variant,
    symbol_keys,
)
from src.symbols import library

UNIVERSAL_KEYS = tuple(symbol.key for symbol in UNIVERSAL_SYMBOLS)

#: Every library entry the symbol authors have marked as having committed
#: artwork — a superset of ``UNIVERSAL_KEYS``, since it also covers
#: destination-flavoured entries like souvlaki that are ``ready`` but not
#: always-findable enough to join the universal pool.
_READY_KEYS = tuple(symbol.key for symbol in library().all() if symbol.facets.status == "ready")


@pytest.mark.parametrize("variant", [IMAGES, CUTOUTS, SILHOUETTES])
def test_every_ready_symbol_has_every_variant(variant):
    """A symbol marked ``status: "ready"`` in the library must be printable in
    all three forms.

    ``status`` is authored by whoever adds the entry — see
    ``src/symbols/model.py`` for why it isn't scanned from disk at runtime —
    and the matching page needs the two derived variants on top of the plain
    drawing, or a key with art but no silhouette prints as a blank in the
    shadow column. Adding a symbol therefore means running
    ``tools/make_shadow_symbols.py`` in the same commit that flips its status.

    A silhouette that came out unrecognisable is the one deliberate
    exception: ``_SHADOW_UNSUITABLE`` (``src/activities/matching.py``) both
    keeps the key out of the matching page and — for this check — waives the
    silhouette requirement, since the file was intentionally deleted rather
    than regenerated. ``images``/``cutouts`` still apply; the plain drawing
    is used by the scavenger hunt regardless.
    """
    required_keys = _READY_KEYS
    if variant == SILHOUETTES:
        required_keys = tuple(key for key in _READY_KEYS if key not in _SHADOW_UNSUITABLE)
    found = find_variant(required_keys, variant)
    missing = sorted(set(required_keys) - set(found))
    assert not missing, (
        f"no {variant}/ artwork for: {', '.join(missing)} — "
        "run python tools/make_shadow_symbols.py"
    )


def test_every_symbol_with_artwork_on_disk_is_in_the_library():
    """The reverse direction: art on disk with no library entry is exactly
    the old "orphan" bug (souvlaki, skis-and-poles, ... were committed and
    reachable by no code path) — this is what stops it recurring."""
    images_dir = DEFAULT_SYMBOL_ROOT / IMAGES
    if not images_dir.is_dir():
        return
    # ``.gitkeep`` (and any other dotfile) is directory-tracking scaffolding,
    # not a symbol drawing — ``Path(".gitkeep").stem`` is the whole filename,
    # so it would otherwise read as an orphaned key named "gitkeep".
    on_disk = {path.stem for path in images_dir.glob("*.*") if not path.name.startswith(".")}
    known = {symbol.key for symbol in library().all()}
    orphaned = sorted(on_disk - known)
    assert not orphaned, f"artwork with no library entry: {orphaned}"


def test_a_drawing_and_its_shadow_are_the_same_size():
    """The one thing the puzzle depends on: both variants come from one crop
    box, so neither column can leak the answer through its proportions."""
    pytest.importorskip("PIL", reason="reading PNG headers needs Pillow")
    from PIL import Image

    cutouts = find_variant(UNIVERSAL_KEYS, CUTOUTS)
    silhouettes = find_variant(UNIVERSAL_KEYS, SILHOUETTES)
    for key, path in cutouts.items():
        if key not in silhouettes:
            continue  # _SHADOW_UNSUITABLE — no silhouette on disk by design
        with Image.open(path) as drawing, Image.open(silhouettes[key]) as shadow:
            assert drawing.size == shadow.size, key


def test_a_missing_variant_is_not_an_error(tmp_path):
    """The derived directories are a cache. A key with no file is a
    placeholder on the page, never an exception."""
    assert find_variant(["nothing-here"], CUTOUTS) == {}
    assert find_variant(UNIVERSAL_KEYS, "no-such-variant", root=tmp_path) == {}


def test_variants_are_matched_by_extension(tmp_path):
    """The image backend saves whatever the model returned, not always a PNG."""
    (tmp_path / IMAGES).mkdir()
    (tmp_path / IMAGES / "stop-sign.webp").write_bytes(b"not really a webp")
    assert find_variant(["stop-sign"], IMAGES, root=tmp_path) == {
        "stop-sign": tmp_path / IMAGES / "stop-sign.webp"
    }


def test_generated_art_wins_over_the_cache(builder):
    """``--generate-images`` hands back what it just produced; that is the
    freshest answer for the plain drawing."""
    from src import generate_workbook

    result = generate_workbook(
        destination="Kfar Hanokdim", children=["Noa"], ages=[6], write=False, builder=builder
    )
    workbook = result.workbook
    key = symbol_keys(workbook)[0]
    fresh = Path("somewhere") / f"{key}.png"

    art = artwork_for(workbook, overrides={key: fresh})
    assert art.images[key] == fresh
    # ...but only for the drawing: the derived variants are produced offline,
    # so a freshly generated symbol genuinely has none yet.
    assert art.silhouettes.get(key) != fresh


def test_the_cache_lives_beside_the_prompts():
    assert (DEFAULT_SYMBOL_ROOT / "prompts").is_dir()
    assert DEFAULT_SYMBOL_ROOT.name == "symbols"


#: A point well inside each subject's own body, as a fraction of the
#: silhouette image's width/height — robust to `--max-side` changing the
#: file's absolute pixel size, unlike a hardcoded coordinate.
#:
#: Originally three keys: a mountain range, a tractor and a train are each
#: drawn with their outline never closing along some edge (no baseline, or a
#: carriage missing its left wall), so plain hole-filling left the interior
#: background-colored instead of shadow-colored — the true background reached
#: it by flowing through the same gap the ink itself never closed. `tractor`
#: and `train` were dropped once their `silhouettes/*.png` were deleted for
#: being unrecognisable as shapes (``_SHADOW_UNSUITABLE`` in
#: `src/activities/matching.py`) — regenerating just to keep this guard alive
#: is exactly what "do not recreate them" rules out; `mountain` alone still
#: exercises the `GROUND_SIDES`/`EXTRA_CLOSE_RADIUS` code path this guards.
_INTERIOR_POINTS = {
    "mountain": (0.5, 0.65),
}


@pytest.mark.parametrize("key", sorted(_INTERIOR_POINTS))
def test_symbols_with_an_open_outline_still_fill_solid(key):
    """Regression guard for `GROUND_SIDES` in `tools/make_shadow_symbols.py`.

    Without it, `binary_fill_holes` alone never marks these points as
    enclosed, because they are not: the true background reaches them by
    flowing around, through whichever edge the drawing leaves open. If this
    ever starts failing after touching that script, check the symbol's own
    `_contact.png` by eye before assuming the fraction just needs updating —
    it might mean the source drawing changed shape.
    """
    pytest.importorskip("PIL", reason="reading pixels needs Pillow")
    from PIL import Image

    path = find_variant([key], SILHOUETTES)[key]
    with Image.open(path) as image:
        width, height = image.size
        fx, fy = _INTERIOR_POINTS[key]
        alpha = image.getpixel((int(width * fx), int(height * fy)))[3]
    assert alpha > 200, f"{key}: interior sample point is not filled solid"
