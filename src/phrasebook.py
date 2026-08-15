"""Strict loading of ``data/phrasebook/<language>.json`` — ten basic words
in a destination's local language, each with a pronunciation spelled in the
*workbook's* language.

Curated and checked in, one file per language, reviewed once — the concept
list is fixed and small enough that a human can actually read the whole
file. This is deliberately not generated at request time: nobody reviews an
LLM's Greek before it prints in a child's book, and the pronunciation column
is exactly where that would fail silently.

The *meaning* of each concept ("thank you") is a locale string
(``phrasebook.concept.<concept>``), not data here — that way it is
automatically correct in the workbook's own language and automatically
clean for ``src/qa.py``. This module only carries the native word and its
pronunciation.

Kept as a standalone leaf module, like ``src/countries.py`` and
``src/fonts.py``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "data" / "phrasebook"

#: The ten concepts every phrasebook must cover, in the fixed order a page
#: prints them — no RNG involved, so the section is byte-reproducible.
CONCEPTS: tuple[str, ...] = (
    "yes", "no", "please", "thank_you", "sorry",
    "good_morning", "good_night", "water", "bathroom", "family",
)

_REQUIRED_ENTRY_KEYS = frozenset({"native", "pronunciation"})


class PhrasebookDataError(ValueError):
    """Raised for anything wrong with a ``data/phrasebook/*.json`` file
    itself — a build-time / test-time failure, never something a generated
    book should have to degrade around."""


@dataclass(frozen=True)
class Phrase:
    """One concept, already resolved for one workbook language."""

    concept: str
    native: str
    pronunciation: str


@dataclass(frozen=True)
class Phrasebook:
    language: str
    script: str
    direction: str
    phrases: tuple[Phrase, ...]


_CACHE: dict[str, "_RawPack"] = {}


@dataclass(frozen=True)
class _RawPack:
    language: str
    script: str
    direction: str
    # concept -> (native, {workbook_language: pronunciation})
    entries: Mapping[str, tuple[str, Mapping[str, str]]]


def _load_raw(language: str, directory: Path) -> "_RawPack | None":
    path = directory / f"{language}.json"
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PhrasebookDataError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PhrasebookDataError(f"{path} is not valid JSON: {exc}") from exc

    for key in ("language", "script", "direction", "entries"):
        if key not in raw:
            raise PhrasebookDataError(f"{path} is missing required field {key!r}")
    if raw["language"] != language:
        raise PhrasebookDataError(
            f"{path} declares language {raw['language']!r}, expected {language!r} "
            "(the filename is the source of truth)"
        )
    if raw["direction"] not in ("ltr", "rtl"):
        raise PhrasebookDataError(f"{path} has an unknown direction {raw['direction']!r}")

    entries_block = raw["entries"]
    if not isinstance(entries_block, dict):
        raise PhrasebookDataError(f"{path} 'entries' must be an object")

    missing_concepts = set(CONCEPTS) - set(entries_block)
    extra_concepts = set(entries_block) - set(CONCEPTS)
    if missing_concepts:
        raise PhrasebookDataError(f"{path} is missing concept(s): {sorted(missing_concepts)}")
    if extra_concepts:
        raise PhrasebookDataError(f"{path} has unknown concept(s): {sorted(extra_concepts)}")

    entries: dict[str, tuple[str, Mapping[str, str]]] = {}
    for concept, entry in entries_block.items():
        if not isinstance(entry, dict):
            raise PhrasebookDataError(f"{path}: entry {concept!r} is not an object")
        extra_keys = set(entry) - _REQUIRED_ENTRY_KEYS
        missing_keys = _REQUIRED_ENTRY_KEYS - set(entry)
        if extra_keys:
            raise PhrasebookDataError(f"{path}: entry {concept!r} has unknown field(s): {sorted(extra_keys)}")
        if missing_keys:
            raise PhrasebookDataError(f"{path}: entry {concept!r} is missing field(s): {sorted(missing_keys)}")
        native = str(entry["native"]).strip()
        if not native:
            raise PhrasebookDataError(f"{path}: entry {concept!r} has an empty native word")
        pronunciation = entry["pronunciation"]
        if not isinstance(pronunciation, dict) or not pronunciation:
            raise PhrasebookDataError(f"{path}: entry {concept!r} has no pronunciation")
        entries[concept] = (native, {str(k): str(v) for k, v in pronunciation.items()})

    return _RawPack(
        language=raw["language"],
        script=raw["script"],
        direction=raw["direction"],
        entries=entries,
    )


def _get_raw(language: str, directory: Path) -> "_RawPack | None":
    cache_key = f"{directory}::{language}"
    if cache_key not in _CACHE:
        pack = _load_raw(language, directory)
        if pack is not None:
            _CACHE[cache_key] = pack
        else:
            return None
    return _CACHE.get(cache_key)


def phrasebook_for(
    language: str,
    *,
    workbook_language: str,
    directory: Path | str | None = None,
) -> Phrasebook | None:
    """The destination-language phrasebook, with every pronunciation
    resolved for ``workbook_language`` — or ``None`` when there is nothing
    usable: no curated file for ``language``, or that file is missing a
    pronunciation for ``workbook_language`` on at least one concept (a half
    -filled table is worse than an omitted section).

    Never raises for a missing or incomplete *pack* — that is exactly the
    "no dictionary for this book" case every caller must already handle.
    Only a malformed file (see :class:`PhrasebookDataError`) is a hard
    failure, the same split ``src/countries.py`` makes.
    """
    if not language:
        return None
    directory = Path(directory) if directory else DEFAULT_DIR
    raw = _get_raw(language, directory)
    if raw is None:
        return None

    workbook_base = (workbook_language or "en").split("-")[0].lower()
    phrases = []
    for concept in CONCEPTS:
        native, pronunciations = raw.entries[concept]
        pronunciation = pronunciations.get(workbook_base)
        if pronunciation is None:
            return None
        phrases.append(Phrase(concept=concept, native=native, pronunciation=pronunciation))

    return Phrasebook(
        language=raw.language, script=raw.script, direction=raw.direction, phrases=tuple(phrases)
    )


def _reset_cache_for_tests() -> None:
    """Test-only escape hatch — nothing in the pipeline calls this."""
    _CACHE.clear()


__all__ = [
    "CONCEPTS",
    "Phrase",
    "Phrasebook",
    "PhrasebookDataError",
    "phrasebook_for",
]
