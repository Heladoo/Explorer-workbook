"""data/phrasebook/<lang>.json: strict load, exactly the ten fixed
concepts, and the language/self-language behaviour phrasebook_for()
promises (see src/phrasebook.py's module docstring)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.locales import en, he
from src.phrasebook import CONCEPTS, DEFAULT_DIR, PhrasebookDataError, phrasebook_for

_WORKBOOK_LANGUAGES = ("en", "he")


def test_at_least_one_phrasebook_is_shipped():
    assert list(DEFAULT_DIR.glob("*.json"))


@pytest.mark.parametrize("path", sorted(DEFAULT_DIR.glob("*.json")), ids=lambda p: p.stem)
def test_every_shipped_pack_has_exactly_the_fixed_concepts(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert set(data["entries"]) == set(CONCEPTS)


@pytest.mark.parametrize("path", sorted(DEFAULT_DIR.glob("*.json")), ids=lambda p: p.stem)
@pytest.mark.parametrize("workbook_language", _WORKBOOK_LANGUAGES)
def test_every_shipped_pack_has_a_pronunciation_for_every_workbook_language(path, workbook_language):
    data = json.loads(path.read_text(encoding="utf-8"))
    for concept, entry in data["entries"].items():
        assert workbook_language in entry["pronunciation"], (
            f"{path.name}:{concept} has no {workbook_language!r} pronunciation"
        )


@pytest.mark.parametrize("path", sorted(DEFAULT_DIR.glob("*.json")), ids=lambda p: p.stem)
def test_every_shipped_pack_loads_via_phrasebook_for(path):
    language = path.stem
    for workbook_language in _WORKBOOK_LANGUAGES:
        if language == workbook_language:
            continue  # the deliberate self-language case, see below
        book = phrasebook_for(language, workbook_language=workbook_language)
        assert book is not None, f"{path.name} failed to load for workbook_language={workbook_language!r}"
        assert [p.concept for p in book.phrases] == list(CONCEPTS)


def test_phrases_are_always_in_concept_order():
    """No RNG anywhere in this module — the section must be byte-identical
    across runs and across workbook languages."""
    book_en = phrasebook_for("el", workbook_language="en")
    book_he = phrasebook_for("el", workbook_language="he")
    assert [p.concept for p in book_en.phrases] == list(CONCEPTS)
    assert [p.concept for p in book_he.phrases] == list(CONCEPTS)
    assert [p.native for p in book_en.phrases] == [p.native for p in book_he.phrases]


def test_returns_none_for_an_unknown_language():
    assert phrasebook_for("xx", workbook_language="en") is None


def test_returns_none_for_an_empty_language():
    assert phrasebook_for("", workbook_language="en") is None


@pytest.mark.parametrize("locale", (en, he), ids=lambda m: m.LANGUAGE)
def test_every_concept_has_a_meaning_string_in_every_locale(locale):
    keys = set(locale.STRINGS)
    for concept in CONCEPTS:
        assert f"phrasebook.concept.{concept}" in keys, concept


# -- strict-loader failure modes ------------------------------------------


def _write(tmp_path: Path, language: str, payload: dict) -> Path:
    path = tmp_path / f"{language}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _minimal_entries(**overrides) -> dict:
    entries = {
        concept: {"native": "x", "pronunciation": {"en": "x", "he": "x"}} for concept in CONCEPTS
    }
    entries.update(overrides)
    return entries


def test_rejects_a_missing_concept(tmp_path):
    entries = _minimal_entries()
    del entries["family"]
    _write(tmp_path, "xx", {"language": "xx", "script": "latin", "direction": "ltr", "entries": entries})
    with pytest.raises(PhrasebookDataError, match="missing concept"):
        phrasebook_for("xx", workbook_language="en", directory=tmp_path)


def test_rejects_an_unknown_concept(tmp_path):
    entries = _minimal_entries()
    entries["goodbye"] = {"native": "x", "pronunciation": {"en": "x"}}
    _write(tmp_path, "xx", {"language": "xx", "script": "latin", "direction": "ltr", "entries": entries})
    with pytest.raises(PhrasebookDataError, match="unknown concept"):
        phrasebook_for("xx", workbook_language="en", directory=tmp_path)


def test_rejects_an_unknown_direction(tmp_path):
    _write(
        tmp_path, "xx",
        {"language": "xx", "script": "latin", "direction": "sideways", "entries": _minimal_entries()},
    )
    with pytest.raises(PhrasebookDataError, match="direction"):
        phrasebook_for("xx", workbook_language="en", directory=tmp_path)


def test_rejects_a_language_mismatch_with_the_filename(tmp_path):
    _write(
        tmp_path, "xx",
        {"language": "yy", "script": "latin", "direction": "ltr", "entries": _minimal_entries()},
    )
    with pytest.raises(PhrasebookDataError, match="filename"):
        phrasebook_for("xx", workbook_language="en", directory=tmp_path)


def test_missing_workbook_pronunciation_returns_none_not_a_partial_table(tmp_path):
    entries = _minimal_entries(water={"native": "x", "pronunciation": {"en": "x"}})  # no "he"
    _write(tmp_path, "xx", {"language": "xx", "script": "latin", "direction": "ltr", "entries": entries})
    assert phrasebook_for("xx", workbook_language="en", directory=tmp_path) is not None
    assert phrasebook_for("xx", workbook_language="he", directory=tmp_path) is None


def test_missing_file_returns_none_not_an_error(tmp_path):
    assert phrasebook_for("zz", workbook_language="en", directory=tmp_path) is None
