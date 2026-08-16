"""The embedded-font manifest is a coverage *contract* — see src/fonts.py's
module docstring for why this can't be checked from a live woff2 read at
runtime (no brotli in the stdlib). These tests are what keeps the manifest
honest instead.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import fonts
from src.phrasebook import DEFAULT_DIR as PHRASEBOOK_DIR

ROOT = Path(__file__).resolve().parents[1]


def test_every_declared_face_has_a_file():
    for face in fonts.FACES:
        path = fonts.FONT_DIR / face.filename
        assert path.is_file(), f"{face.filename} (family {face.family!r}) is declared but missing"


def test_every_face_declares_a_unicode_range():
    for face in fonts.FACES:
        assert face.unicode_range, f"{face.filename} has no unicode-range"
        assert fonts.parse_unicode_range(face.unicode_range), (
            f"{face.filename}'s unicode-range {face.unicode_range!r} didn't parse to anything"
        )


def test_base_faces_cover_every_family_named_in_the_css_stacks():
    """Every family a CSS ``--font-*`` stack names as its *first* choice
    (the one every book should actually render in) must be a base face —
    i.e. embedded in every book, not gated behind a script that happens not
    to appear. A first-choice family that were script-gated would silently
    fall through to the *next* name in the stack for a plain book, which is
    exactly the failure this whole manifest exists to prevent."""
    base_families = {face.family for face in fonts.FACES if face.script is None}
    assert base_families == {
        "Baloo 2", "Nunito", "Secular One", "Assistant", "JetBrains Mono",
    }


def test_declared_coverage_includes_every_shipped_phrasebook_script():
    """The 'fail loudly' gate: a phrasebook for a script with no embedded
    font must fail here, at test time — not print tofu boxes in a shipped
    book. Adding data/phrasebook/<lang>.json for a new script means adding
    that script's face(s) to src/fonts.py in the same change."""
    scripts_in_use = set()
    for path in sorted(PHRASEBOOK_DIR.glob("*.json")):
        pack = json.loads(path.read_text(encoding="utf-8"))
        scripts_in_use.add(pack["script"])
    assert scripts_in_use, "expected at least one shipped phrasebook"
    for script in scripts_in_use:
        assert fonts.covers_script(script), (
            f"a phrasebook uses script {script!r}, which has no embedded font face"
        )


def test_every_phrasebook_character_is_embedded():
    """Stronger than the script-level check above: catches a stray
    character (a curly quote, a rare diacritic) that a script's *declared*
    range happens to miss, even though the script overall is covered."""
    for path in sorted(PHRASEBOOK_DIR.glob("*.json")):
        pack = json.loads(path.read_text(encoding="utf-8"))
        script = pack["script"]
        covered = frozenset({script})
        for concept, entry in pack["entries"].items():
            missing = fonts.missing_characters(entry["native"], scripts=covered)
            assert not missing, f"{path.name}:{concept} native word has uncovered characters {missing}"
            for lang, pronunciation in entry["pronunciation"].items():
                missing = fonts.missing_characters(pronunciation, scripts=None)
                assert not missing, (
                    f"{path.name}:{concept} pronunciation[{lang}] has uncovered characters {missing}"
                )


def test_scripts_in_detects_every_covered_script():
    """One representative character per script this repo ships a face for,
    round-tripped through scripts_in() — guards against the kind of range
    mixup that silently broke Czech detection during development (Latin
    Extended-A was folded into the base 'latin' block instead of
    'latin_ext', so scripts_in() reported nothing needed for a word with a
    'ě' in it)."""
    samples = {
        "greek": "α",  # alpha
        "cyrillic": "а",  # a
        "latin_ext": "ě",  # e with caron
        "hebrew": "ש",  # shin
    }
    for script, char in samples.items():
        assert fonts.scripts_in(char) == frozenset({script}), script


def test_scripts_in_needs_nothing_for_plain_ascii():
    assert fonts.scripts_in("Hello, world! 123") == frozenset()


def test_covers_script_is_false_for_an_uncovered_script():
    assert fonts.covers_script("thai") is False


def test_font_faces_raises_on_a_missing_file(tmp_path):
    from src.rendering.templates import TemplateSet

    # A template dir with no assets/fonts directory at all -- every face's
    # asset_data_uri() lookup fails, which must raise, not silently embed
    # nothing (the historical bug this replaced -- see templates.py).
    templates = TemplateSet(tmp_path)
    with pytest.raises(FileNotFoundError):
        templates.font_faces()


def test_declared_ranges_match_the_real_font_files():
    """The manifest's own guarantee, checked against the actual bytes: a
    declared unicode-range must be a subset of what the shipped file really
    contains, or the "contract" in src/fonts.py is just an assertion nobody
    verifies. Gated on fontTools+brotli like the Playwright tests are gated
    on Chromium — neither is a project dependency, so this test (only this
    one — importorskip inside the test body, not at module level, so it
    can't skip every other test in this file along with it) is opt-in."""
    pytest.importorskip("brotli", reason="woff2 decoding needs the brotli extension")
    pytest.importorskip("fontTools", reason="fontTools not installed")
    from fontTools.ttLib import TTFont

    for face in fonts.FACES:
        path = fonts.FONT_DIR / face.filename
        font = TTFont(str(path))
        cmap = set(font.getBestCmap() or {})
        declared = fonts.parse_unicode_range(face.unicode_range)
        # The meaningful assertion: the file must actually contain *some*
        # of what it claims, for every declared sub-range. Sampled rather
        # than exhaustive for a range spanning thousands of codepoints
        # (e.g. a CJK-sized block) -- the goal is catching a materially
        # wrong range, not auditing every unassigned codepoint in it.
        for low, high in declared:
            span = range(low, high + 1)
            sample = [cp for cp in span if cp in cmap]
            unassigned_is_plausible = high - low > 500  # e.g. a whole CJK-sized block
            assert sample or unassigned_is_plausible, (
                f"{face.filename} declares U+{low:04X}-{high:04X} but the font has none of it"
            )
