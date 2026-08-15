"""Strict loading of ``data/symbols/library.json`` into a queryable :class:`Library`.

Deliberately stricter than ``DestinationKnowledge.from_dict`` (which drops
unknown keys on purpose, because a destination pack is content and may be
incomplete): the symbol library is first-party structure, and a misspelt
``"enviroments"`` here would silently change what every book picks with
nothing ever going red. An unknown field, an unknown tag value, a duplicate
key, or a key that isn't already a slug all raise.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.models.context import slugify
from src.symbols.model import Symbol, SymbolFacets
from src.symbols.vocab import (
    CLIMATES,
    ENVIRONMENTS,
    REGIONS,
    REQUIRED_KEYS,
    ROLES,
    STATUS,
    TOPICS,
    UBIQUITY,
)

#: Every field a library entry may set, mapped to the closed vocabulary it is
#: validated against. ``None`` means free text, not a tag.
_FIELDS: dict[str, tuple[str, ...] | None] = {
    "label": None,
    "subject": None,
    "topic": TOPICS,
    "ubiquity": UBIQUITY,
    "status": STATUS,
    "environments": ENVIRONMENTS,
    "climate": CLIMATES,
    "regions": REGIONS,
    "roles": ROLES,
    "aliases": None,
}

_REQUIRED_FIELDS = ("label", "subject", "topic", "ubiquity", "status")


class LibraryError(ValueError):
    """The library file is malformed."""


class Library:
    """An immutable, key-ordered set of :class:`Symbol` entries."""

    def __init__(self, symbols: tuple[Symbol, ...]) -> None:
        self._symbols = symbols
        self._by_key = {symbol.key: symbol for symbol in symbols}

    def all(self) -> tuple[Symbol, ...]:
        """Every entry, in the order the library file listed them."""
        return self._symbols

    def universal_pool(self) -> tuple[Symbol, ...]:
        """Ready, always-findable entries — the pool the scavenger hunt and
        the matching page have always drawn from.

        Deliberately not every ``ready`` entry: a ``local``/``regional``
        symbol like souvlaki has artwork but is findable-in-Greece, not
        findable-anywhere, and this pool's whole job is the always-findable
        backbone an easy hunt needs to stay finishable on any trip.
        """
        return tuple(
            symbol
            for symbol in self._symbols
            if symbol.facets is not None
            and symbol.facets.status == "ready"
            and symbol.facets.ubiquity in ("everywhere", "common")
        )

    def missing_art(self) -> tuple[str, ...]:
        """Keys still marked ``draft`` — the symbols that need artwork next."""
        return tuple(
            symbol.key
            for symbol in self._symbols
            if symbol.facets is not None and symbol.facets.status == "draft"
        )

    def __getitem__(self, key: str) -> Symbol:
        return self._by_key[key]

    def __contains__(self, key: str) -> bool:
        return key in self._by_key

    def __len__(self) -> int:
        return len(self._symbols)

    def subject(self, key: str) -> str:
        """The English drawing subject for ``key``.

        Raises rather than falling back: a caller naming a key by hand (as
        ``maze.py`` does for its start icon) is asserting that key exists,
        and a silent fallback would print a placeholder nobody notices.
        """
        return self._by_key[key].subject


def load_library(path: Path | str) -> Library:
    """Load the library from a JSON file, or every ``*.json`` in a directory.

    A directory's files are merged in sorted order; a key repeated across two
    files is an error. Accepting a directory from day one means splitting the
    single ``library.json`` into per-topic shards later needs no code change
    here — only a new path.
    """
    root = Path(path)
    sources = sorted(root.glob("*.json")) if root.is_dir() else [root]

    rows: list[dict[str, Any]] = []
    origin: dict[str, Path] = {}
    for source in sources:
        payload = json.loads(source.read_text(encoding="utf-8"))
        entries = payload.get("symbols", payload) if isinstance(payload, dict) else payload
        if not isinstance(entries, list):
            raise LibraryError(f"{source}: expected a list of symbol entries")
        for row in entries:
            key = row.get("key")
            if not isinstance(key, str) or not key:
                raise LibraryError(f"{source}: entry with no string 'key': {row!r}")
            if key in origin:
                raise LibraryError(
                    f"duplicate symbol key {key!r} in {source} and {origin[key]}"
                )
            if slugify(key) != key:
                raise LibraryError(f"{source}: key {key!r} is not already a slug")
            origin[key] = source
            rows.append(row)

    symbols = tuple(_build_symbol(row, source=origin[row["key"]]) for row in rows)
    _check_required_keys(symbols)
    _check_aliases(symbols)
    return Library(symbols)


def _build_symbol(row: Mapping[str, Any], *, source: Path) -> Symbol:
    key = row["key"]
    unknown = set(row) - {"key", *_FIELDS}
    if unknown:
        raise LibraryError(f"{source}: symbol {key!r} has unknown field(s): {sorted(unknown)}")
    missing = [field for field in _REQUIRED_FIELDS if field not in row]
    if missing:
        raise LibraryError(f"{source}: symbol {key!r} is missing required field(s): {missing}")

    for field, vocabulary in _FIELDS.items():
        if vocabulary is None or field not in row:
            continue
        value = row[field]
        values = value if isinstance(value, list) else [value]
        bad = sorted(set(values) - set(vocabulary))
        if bad:
            raise LibraryError(
                f"{source}: symbol {key!r} field {field!r} has unknown tag(s) {bad} "
                f"— valid values are {vocabulary}"
            )

    facets = SymbolFacets(
        topic=row["topic"],
        ubiquity=row["ubiquity"],
        status=row["status"],
        environments=tuple(row.get("environments", ())),
        climate=tuple(row.get("climate", ())),
        regions=tuple(row.get("regions", ())),
        roles=tuple(row.get("roles", ())),
        aliases=tuple(row.get("aliases", ())),
    )
    return Symbol(key=key, label=row["label"], subject=row["subject"], facets=facets)


def _check_required_keys(symbols: tuple[Symbol, ...]) -> None:
    present = {symbol.key for symbol in symbols}
    missing = [key for key in REQUIRED_KEYS if key not in present]
    if missing:
        raise LibraryError(f"library is missing required key(s): {missing}")


def _check_aliases(symbols: tuple[Symbol, ...]) -> None:
    keys = {symbol.key for symbol in symbols}
    claimed_by: dict[str, str] = {}
    for symbol in symbols:
        assert symbol.facets is not None  # every loaded entry has facets
        for alias in symbol.facets.aliases:
            if alias in keys:
                raise LibraryError(
                    f"alias {alias!r} on {symbol.key!r} collides with a real symbol key"
                )
            if alias in claimed_by:
                raise LibraryError(
                    f"alias {alias!r} claimed by both {claimed_by[alias]!r} and {symbol.key!r}"
                )
            claimed_by[alias] = symbol.key
