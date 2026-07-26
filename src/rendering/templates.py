"""Loads and caches the print templates.

Templates use :class:`string.Template` for the same reason the rest of the
project does: no dependency, and a designer can edit the markup without
reading any Python.
"""

from __future__ import annotations

import html
from pathlib import Path
from string import Template
from typing import Any

DEFAULT_PDF_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates" / "pdf"


class TemplateSet:
    """A directory of templates, loaded once and reused."""

    def __init__(self, template_dir: Path | str | None = None) -> None:
        self.template_dir = Path(template_dir) if template_dir else DEFAULT_PDF_TEMPLATE_DIR
        self._cache: dict[str, Template] = {}

    def get(self, name: str) -> Template:
        """Load ``<name>.html.tmpl`` from the template directory."""
        if name not in self._cache:
            path = self.template_dir / f"{name}.html.tmpl"
            if not path.is_file():
                raise FileNotFoundError(f"missing template {path}")
            self._cache[name] = Template(path.read_text(encoding="utf-8"))
        return self._cache[name]

    def has(self, name: str) -> bool:
        return (self.template_dir / f"{name}.html.tmpl").is_file()

    def render(self, name: str, /, **values: Any) -> str:
        """Render a template, HTML-escaping every substituted value.

        ``name`` is positional-only so a template may use ``$name`` as a
        placeholder.

        Values whose key ends in ``_html`` are treated as already-rendered
        markup and passed through — that is how nested fragments compose.
        """
        prepared = {
            key: value if _is_markup(key) else esc(value) for key, value in values.items()
        }
        return self.get(name).substitute(**prepared)

    def read_asset(self, filename: str) -> str:
        """Read a non-template asset, such as ``book.css``."""
        return (self.template_dir / filename).read_text(encoding="utf-8")


#: Suffixes that mark a value as trusted markup rather than text to escape.
_MARKUP_KEYS = ("body", "art", "items", "rows", "options", "cards", "panels",
                "prompts", "stars", "lines", "left", "right", "pages", "contents", "css",
                "cells", "words", "across", "down")


def _is_markup(key: str) -> bool:
    return key in _MARKUP_KEYS


def esc(value: Any) -> str:
    """Escape a value for safe inclusion in HTML."""
    return html.escape(str(value), quote=True)
