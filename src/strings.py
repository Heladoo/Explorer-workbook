"""User-facing copy, kept out of the generators.

Every string a child or parent reads lives in a locale module under
:mod:`src.locales`. Adding a language means adding one file there — no
generator changes. Image prompts are deliberately *not* localized: they are
written in English because that is what image models are trained on, and the
workbook records that in its metadata.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

DEFAULT_LANGUAGE = "en"

_LOCALES: dict[str, Mapping[str, Any]] = {}


def _load_locales() -> dict[str, Mapping[str, Any]]:
    """Import every locale module once and index it by language code."""
    if _LOCALES:
        return _LOCALES
    from src import locales

    for module_info in pkgutil.iter_modules(locales.__path__):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{locales.__name__}.{module_info.name}")
        language = getattr(module, "LANGUAGE", module_info.name)
        _LOCALES[language] = getattr(module, "STRINGS", {})
    return _LOCALES


@dataclass(frozen=True)
class Strings:
    """Copy for one language, with a recorded fallback if it was unavailable."""

    language: str
    requested_language: str
    table: Mapping[str, Any]

    @property
    def is_fallback(self) -> bool:
        return self.language != self.requested_language

    def text(self, key: str, **kwargs: Any) -> str:
        """Look up ``key`` and interpolate ``kwargs`` into it."""
        value = self.table.get(key)
        if value is None:
            raise KeyError(f"missing string {key!r} for language {self.language!r}")
        if not isinstance(value, str):
            raise TypeError(f"string {key!r} is a {type(value).__name__}, use items()")
        try:
            return value.format(**kwargs)
        except KeyError as exc:
            raise KeyError(f"string {key!r} needs placeholder {exc.args[0]!r}") from exc

    def items(self, key: str) -> tuple[str, ...]:
        """Look up a list-valued entry, such as a pool of packing items."""
        value = self.table.get(key)
        if value is None:
            raise KeyError(f"missing string list {key!r} for language {self.language!r}")
        if isinstance(value, str):
            raise TypeError(f"string {key!r} is text, use text()")
        return tuple(value)

    def join(self, values: Sequence[str]) -> str:
        """Join values into a readable list: ``"a, b and c"``."""
        values = [value for value in values if value]
        if not values:
            return ""
        if len(values) == 1:
            return values[0]
        conjunction = self.table.get("common.and", "and")
        return f"{', '.join(values[:-1])} {conjunction} {values[-1]}"


def strings_for(language: str | None) -> Strings:
    """Return the copy for ``language``, falling back to English."""
    requested = (language or DEFAULT_LANGUAGE).strip() or DEFAULT_LANGUAGE
    table = _load_locales()
    # "he-IL" should find the "he" locale.
    for candidate in (requested, requested.split("-")[0].lower()):
        if candidate in table:
            return Strings(language=candidate, requested_language=requested, table=table[candidate])
    return Strings(
        language=DEFAULT_LANGUAGE,
        requested_language=requested,
        table=table[DEFAULT_LANGUAGE],
    )


def available_languages() -> tuple[str, ...]:
    return tuple(sorted(_load_locales()))
