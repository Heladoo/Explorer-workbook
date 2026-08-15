"""The faceted symbol library: what can be drawn, and where it belongs.

Replaces the old comment-out convention in ``src/activities/_symbols.py``
(an entry with no artwork was commented out by hand, so it couldn't be
selected and trigger a paid image call) with an authored ``status`` field —
see :mod:`src.symbols.model` — and adds the facets a destination-relevance
score will need: ``topic``, ``ubiquity``, ``environments``, ``climate``,
``regions``, ``roles``. Scoring itself is not built yet; this package only
captures the factors it will read. See ``src.symbols.vocab`` for the closed
vocabulary those facets draw from.

``library()`` is the one entry point most callers need — a lazily loaded,
process-wide :class:`~src.symbols.loader.Library`.
"""

from __future__ import annotations

from pathlib import Path

from src.symbols.loader import Library, LibraryError, load_library
from src.symbols.model import Symbol, SymbolFacets
from src.symbols.vocab import REQUIRED_KEYS

#: Repo root / data / symbols — a sibling of data/destinations.
DEFAULT_LIBRARY_PATH = Path(__file__).resolve().parents[2] / "data" / "symbols" / "library.json"

_library: Library | None = None


def library(path: Path | str = DEFAULT_LIBRARY_PATH) -> Library:
    """The process-wide symbol library, loaded once and cached.

    A non-default ``path`` bypasses the cache (used by tests that load a
    deliberately shuffled or malformed library) but never overwrites it —
    the cache always holds whatever the *default* path last produced.
    """
    global _library
    if path != DEFAULT_LIBRARY_PATH:
        return load_library(path)
    if _library is None:
        _library = load_library(path)
    return _library


def missing_art() -> tuple[str, ...]:
    """Keys still marked ``draft`` in the default library — the symbols that
    need artwork next. A plain data query, safe to call from a REPL or a
    future ``tools/`` script without committing anything."""
    return library().missing_art()


__all__ = [
    "DEFAULT_LIBRARY_PATH",
    "Library",
    "LibraryError",
    "REQUIRED_KEYS",
    "Symbol",
    "SymbolFacets",
    "library",
    "load_library",
    "missing_art",
]
