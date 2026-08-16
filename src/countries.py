"""Strict loading of ``data/countries.json`` into a queryable table of
country facts — capital, continent, currency, spoken language(s) and flag
colours.

This is first-party structure, not authored destination content, so it is
deliberately stricter than ``DestinationKnowledge.from_dict``: an unknown
key, an unknown vocabulary token (a continent, colour or currency the locale
modules don't know how to translate) or a duplicate country code all raise
at load time rather than surfacing as a wrong or missing word in a printed
book. Same posture as ``src/symbols/loader.py``.

Every value is a token, never display text — ``"capital": "athens"``, not
``"Athens"``. Display text is a locale's job (``place.athens``,
``country.greece``, ...), so adding Hebrew for every country here is "add
one locale file", the same principle already used for the symbol library.

Kept as a standalone leaf module — no imports from elsewhere in ``src`` — so
an activity can call :func:`country_for` directly without ``src.models.context``
needing to know this module exists (the "never touch the filesystem" rule in
``CLAUDE.md`` is about generated *output*; reading a curated, checked-in data
file is exactly what ``src/symbols/loader.py`` and ``src/activities/maze.py``
already do for the symbol library).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "countries.json"

#: Closed vocabularies a country's fields are validated against. A value
#: outside these raises at load time rather than reaching a locale lookup
#: that silently falls back to an untranslated English default.
CONTINENTS = ("europe", "asia", "africa", "north_america", "south_america", "oceania")
COLOURS = ("red", "blue", "white", "green", "yellow", "black", "orange", "gold")

_REQUIRED_KEYS = frozenset({"name", "capital", "continent", "currency", "languages", "flag_colours"})


class CountryDataError(ValueError):
    """Raised for anything wrong with ``data/countries.json`` itself — this
    is a build-time / test-time failure, never something a generated book
    should have to degrade around."""


@dataclass(frozen=True)
class CountryFacts:
    """One country's facts, in token form — resolve to display text through
    a locale's ``country.*`` / ``place.*`` / ``continent.*`` / ``currency.*``
    / ``colour.*`` / ``language.*`` keys."""

    code: str
    name: str
    capital: str
    continent: str
    currency: str
    languages: tuple[str, ...]
    flag_colours: tuple[str, ...]

    @property
    def primary_language(self) -> str:
        return self.languages[0] if self.languages else ""


_CACHE: dict[str, CountryFacts] | None = None


def _load(path: Path | str | None = None) -> dict[str, CountryFacts]:
    source = Path(path) if path else DEFAULT_PATH
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CountryDataError(f"cannot read {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CountryDataError(f"{source} is not valid JSON: {exc}") from exc

    countries_block = raw.get("countries")
    if not isinstance(countries_block, dict):
        raise CountryDataError(f"{source} has no top-level 'countries' object")

    result: dict[str, CountryFacts] = {}
    for code, entry in countries_block.items():
        if not isinstance(code, str) or not code.isalpha() or code != code.upper():
            raise CountryDataError(f"country key {code!r} is not an uppercase alpha code")
        if code in result:
            raise CountryDataError(f"duplicate country code {code!r}")
        if not isinstance(entry, dict):
            raise CountryDataError(f"country {code!r} is not an object")

        extra = set(entry) - _REQUIRED_KEYS
        if extra:
            raise CountryDataError(f"country {code!r} has unknown field(s): {sorted(extra)}")
        missing = _REQUIRED_KEYS - set(entry)
        if missing:
            raise CountryDataError(f"country {code!r} is missing field(s): {sorted(missing)}")

        continent = entry["continent"]
        if continent not in CONTINENTS:
            raise CountryDataError(f"country {code!r} has unknown continent {continent!r}")

        flag_colours = tuple(entry["flag_colours"])
        if not flag_colours:
            raise CountryDataError(f"country {code!r} has no flag_colours")
        bad_colours = [c for c in flag_colours if c not in COLOURS]
        if bad_colours:
            raise CountryDataError(f"country {code!r} has unknown flag colour(s): {bad_colours}")

        languages = tuple(entry["languages"])
        if not languages:
            raise CountryDataError(f"country {code!r} has no languages")

        result[code] = CountryFacts(
            code=code,
            name=str(entry["name"]),
            capital=str(entry["capital"]),
            continent=continent,
            currency=str(entry["currency"]),
            languages=languages,
            flag_colours=flag_colours,
        )
    return result


def countries(path: Path | str | None = None) -> Mapping[str, CountryFacts]:
    """Every curated country, keyed by its ISO 3166-1 alpha-2 code.

    Loaded once and cached — ``path`` is only for tests that want an
    isolated fixture file; the default call (no argument) always shares one
    cached table, matching ``src/symbols/loader.py``'s ``load_library()``.
    """
    global _CACHE
    if path is not None:
        return _load(path)
    if _CACHE is None:
        _CACHE = _load()
    return _CACHE


def country_for(code: str, path: Path | str | None = None) -> CountryFacts | None:
    """Look up one country by its code, or ``None`` for an unknown/empty code.

    Never raises for a bad *code* — an empty or unrecognised code just means
    "no country data for this destination", which every caller must already
    handle gracefully (a pack with no ``country`` field, or one naming a
    country not yet in ``data/countries.json``). Only the data file itself
    being malformed is a hard failure (see :class:`CountryDataError`).
    """
    if not code:
        return None
    return countries(path).get(code.upper())


def _reset_cache_for_tests() -> None:
    """Test-only escape hatch — nothing in the pipeline calls this."""
    global _CACHE
    _CACHE = None


__all__ = [
    "COLOURS",
    "CONTINENTS",
    "CountryDataError",
    "CountryFacts",
    "countries",
    "country_for",
]
