"""The embedded-font manifest: what is checked in, and which script each
file covers.

The printed HTML/PDF is rendered by whatever Chromium build happens to be on
the machine running it, so every glyph the workbook actually prints must be
embedded rather than named and hoped for (see ``src/rendering/templates.py``,
which turns this manifest into ``@font-face`` rules).

This module is the *declared* half of that guarantee: a table of faces, each
tagged with the script it covers, plus helpers to work out which scripts a
piece of rendered text needs and whether this repository ships a face for
it. It deliberately does not — cannot — read a live decision from the woff2
files themselves: woff2 is Brotli-compressed and there is no ``brotli`` in
the standard library, so verifying the manifest against the real files is a
job for an optional test (``tests/test_fonts.py``, gated on ``fontTools``
being installed), not for runtime code.

Kept as a standalone leaf module (no imports from elsewhere in ``src``) so
both ``src.rendering.templates`` and any activity that needs to know whether
a script is covered can import it without a cycle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent / "templates" / "pdf" / "assets" / "fonts"

#: Every script this repository ships a checked-in cut for. A script not in
#: here has no embedded coverage at all, whatever a face's unicode-range
#: happens to claim.
SCRIPTS = ("latin", "latin_ext", "greek", "cyrillic", "hebrew")

#: Approximate block for each script, used to decide which packs a piece of
#: rendered text needs (``scripts_in``). Deliberately generous rather than
#: exact — a false positive just embeds one extra pack; a false negative
#: prints an unembedded glyph, which is the failure this module exists to
#: prevent, so ranges lean wide.
#:
#: ``"latin"`` is deliberately narrow — U+0000-00FF plus the handful of
#: punctuation/symbol codepoints the base faces' own Google Fonts "latin"
#: cut declares (see ``_LATIN_RANGE`` below) — because it stands for "the
#: base UI faces, always embedded, already cover this" rather than "the
#: Latin script" in the Unicode sense. Latin Extended-A (U+0100-024F, which
#: is where Czech's ě/č/ř and most other Latin diacritics live) is *not*
#: covered by the base faces, so it belongs to ``"latin_ext"`` instead —
#: conflating the two here previously made ``scripts_in`` silently treat an
#: uncovered Czech word as needing nothing.
_SCRIPT_BLOCKS: dict[str, tuple[tuple[int, int], ...]] = {
    "latin": ((0x0000, 0x00FF), (0x2000, 0x206F), (0x20AC, 0x20AC), (0x2122, 0x2122)),
    "latin_ext": ((0x0100, 0x02FF), (0x1E00, 0x1EFF), (0x2C60, 0x2C7F), (0xA720, 0xA7FF)),
    "greek": ((0x0370, 0x03FF), (0x1F00, 0x1FFF)),
    "cyrillic": ((0x0400, 0x04FF), (0x2DE0, 0x2DFF), (0xA640, 0xA69F)),
    "hebrew": ((0x0590, 0x05FF), (0xFB1D, 0xFB4F)),
}


@dataclass(frozen=True)
class FontFace:
    """One ``@font-face`` rule: a family, a weight, a file, and the script
    it covers (``None`` for a base face embedded in every book)."""

    family: str
    filename: str
    weight: int
    unicode_range: str
    script: str | None  # None = always embedded, part of the base UI faces


#: Approximate Hebrew block, matching the Google Fonts "hebrew" subset used
#: when the Latin and Hebrew cuts of a family were downloaded separately.
_HEBREW_RANGE = "U+0590-05FF, U+FB1D-FB4F, U+20AA"

#: Google Fonts' own Latin cut for a UI family — what every non-subsetted
#: face in this project already covers. Recorded explicitly (rather than
#: left as ``None``) so the manifest is a complete coverage contract: every
#: face declares what it covers, with nothing left implicit.
_LATIN_RANGE = (
    "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+2000-206F, U+2074, "
    "U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215"
)

#: Noto Sans' own cuts, fetched from Google Fonts (see the six
#: ``NotoSans-*-{greek,cyrillic,latin-ext}.woff2`` files under
#: ``assets/fonts/``) — kept as the literal ranges Google Fonts declares
#: rather than the wider ``_SCRIPT_BLOCKS`` scan ranges above, because these
#: describe a specific shipped file rather than "does this book need the
#: pack at all".
_LATIN_EXT_RANGE = (
    "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, "
    "U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, "
    "U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF"
)
_GREEK_RANGE = "U+0370-0377, U+037A-037F, U+0384-038A, U+038C, U+038E-03A1, U+03A3-03FF"
_CYRILLIC_RANGE = "U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116"

#: Every embeddable face. ``script=None`` faces are the base UI set, always
#: embedded regardless of what a book needs — their family names appear in
#: every CSS stack (see book.css's ``--font-*`` tokens), so dropping them
#: would break every book, not just ones missing a script.
FACES: tuple[FontFace, ...] = (
    FontFace("Baloo 2", "Baloo2-Bold.woff2", 700, _LATIN_RANGE, None),
    FontFace("Baloo 2", "Baloo2-ExtraBold.woff2", 800, _LATIN_RANGE, None),
    FontFace("Nunito", "Nunito-Regular.woff2", 400, _LATIN_RANGE, None),
    FontFace("Nunito", "Nunito-SemiBold.woff2", 600, _LATIN_RANGE, None),
    FontFace("Nunito", "Nunito-Bold.woff2", 700, _LATIN_RANGE, None),
    FontFace("Secular One", "SecularOne-Regular.woff2", 400, _LATIN_RANGE, None),
    FontFace("Assistant", "Assistant-Regular.woff2", 400, _LATIN_RANGE, None),
    FontFace("Assistant", "Assistant-Bold.woff2", 700, _LATIN_RANGE, None),
    FontFace("JetBrains Mono", "JetBrainsMono-Regular.woff2", 400, _LATIN_RANGE, None),
    # -- on demand, tagged by script --------------------------------------
    FontFace("Secular One", "SecularOne-Regular-hebrew.woff2", 400, _HEBREW_RANGE, "hebrew"),
    FontFace("Assistant", "Assistant-Regular-hebrew.woff2", 400, _HEBREW_RANGE, "hebrew"),
    FontFace("Assistant", "Assistant-Bold-hebrew.woff2", 700, _HEBREW_RANGE, "hebrew"),
    FontFace("Noto Sans", "NotoSans-Regular-greek.woff2", 400, _GREEK_RANGE, "greek"),
    FontFace("Noto Sans", "NotoSans-Bold-greek.woff2", 700, _GREEK_RANGE, "greek"),
    FontFace("Noto Sans", "NotoSans-Regular-cyrillic.woff2", 400, _CYRILLIC_RANGE, "cyrillic"),
    FontFace("Noto Sans", "NotoSans-Bold-cyrillic.woff2", 700, _CYRILLIC_RANGE, "cyrillic"),
    FontFace("Noto Sans", "NotoSans-Regular-latin-ext.woff2", 400, _LATIN_EXT_RANGE, "latin_ext"),
    FontFace("Noto Sans", "NotoSans-Bold-latin-ext.woff2", 700, _LATIN_EXT_RANGE, "latin_ext"),
)

#: Scripts with at least one checked-in face — the "fail loudly" boundary.
#: A script not in here has no embedded coverage, whatever a caller asks for.
COVERED_SCRIPTS: frozenset[str] = frozenset(
    face.script for face in FACES if face.script is not None
)

_RANGE_TOKEN = re.compile(r"U\+([0-9A-Fa-f]+)(?:-([0-9A-Fa-f]+))?")


def parse_unicode_range(text: str) -> tuple[tuple[int, int], ...]:
    """Parse a CSS ``unicode-range`` value into ``(start, end)`` codepoint
    pairs. Tolerant of the ``U+XXXX-YYYY`` and single-codepoint ``U+XXXX``
    forms; anything else is ignored rather than raised, since this is used
    on values this module itself authored."""
    ranges = []
    for start, end in _RANGE_TOKEN.findall(text):
        low = int(start, 16)
        high = int(end, 16) if end else low
        ranges.append((low, high))
    return tuple(ranges)


def covers_script(script: str) -> bool:
    """Whether this repository ships an embeddable face for ``script``.

    ``"latin"`` is always covered without appearing in ``COVERED_SCRIPTS``:
    it is what the *base* faces (``script=None`` in ``FACES``) already
    provide in every book, never a gated on-demand pack — the same reason
    ``scripts_in()`` never asks for it. A caller checking a phrasebook's
    script (e.g. ``data/phrasebook/en.json``, ``"script": "latin"``, for an
    English-speaking destination) needs this to be ``True`` unconditionally,
    or a perfectly printable English word list would be silently omitted.
    """
    if script == "latin":
        return True
    return script in COVERED_SCRIPTS


def _script_of(codepoint: int) -> str | None:
    for script, blocks in _SCRIPT_BLOCKS.items():
        for low, high in blocks:
            if low <= codepoint <= high:
                return script
    return None


def scripts_in(text: str) -> frozenset[str]:
    """Which script packs ``text`` needs embedded to print without falling
    back to a system font.

    Plain ASCII needs nothing extra (the base faces already cover Latin);
    everything else is attributed to the widest-matching script block it
    falls in. Scanning the *rendered* output rather than a destination's
    declared language is deliberate: it is impossible for a character to
    reach the page without its script being detected here, whatever put it
    there — a stray word, a mistranslation, a future activity nobody
    updated this module for.
    """
    needed: set[str] = set()
    for char in text:
        codepoint = ord(char)
        if codepoint < 0x0080:  # plain ASCII: every base face has this
            continue
        script = _script_of(codepoint)
        if script and script != "latin":
            needed.add(script)
    return frozenset(needed)


def missing_characters(text: str, scripts: frozenset[str] | None = None) -> tuple[str, ...]:
    """Characters in ``text`` that fall outside every covered face's
    declared range — i.e. would fall back to a system font even after
    embedding everything ``scripts_in(text)`` asks for.

    ``scripts`` restricts which on-demand packs are considered "embedded"
    for this check; omit it to check against every face this repo ships.
    """
    covered_ranges: list[tuple[int, int]] = []
    for face in FACES:
        if face.script is not None and scripts is not None and face.script not in scripts:
            continue
        covered_ranges.extend(parse_unicode_range(face.unicode_range))

    def is_covered(codepoint: int) -> bool:
        return any(low <= codepoint <= high for low, high in covered_ranges)

    missing = []
    for char in text:
        if char.isspace():
            continue
        if not is_covered(ord(char)) and char not in missing:
            missing.append(char)
    return tuple(missing)


__all__ = [
    "COVERED_SCRIPTS",
    "FACES",
    "FONT_DIR",
    "FontFace",
    "SCRIPTS",
    "covers_script",
    "missing_characters",
    "parse_unicode_range",
    "scripts_in",
]
