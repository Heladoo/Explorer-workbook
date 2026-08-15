"""Loads and caches the print templates.

Templates use :class:`string.Template` for the same reason the rest of the
project does: no dependency, and a designer can edit the markup without
reading any Python.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path
from string import Template
from typing import Any

from src.fonts import FACES

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
        """Read a non-template text asset, such as ``book.css``."""
        return (self.template_dir / filename).read_text(encoding="utf-8")

    def asset_data_uri(self, relative_path: str, mime: str) -> str | None:
        """A binary asset (e.g. the logo) as an inline ``data:`` URI, or
        ``None`` if it isn't there — the caller decides whether that's fatal."""
        path = self.template_dir / relative_path
        if not path.is_file():
            return None
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    def font_faces(self, scripts: frozenset[str] | None = None) -> str:
        """``@font-face`` rules for every embedded workbook typeface, inlined
        as base64 the same way :meth:`asset_data_uri` inlines the logo.

        The printed HTML/PDF must render identically on every machine, so no
        family here is ever left to a system fallback — ``PdfRenderer`` prints
        through whatever Chromium build happens to be installed, and that
        build's font set is not something this project controls.

        ``scripts`` selects which *on-demand* faces (see ``src/fonts.py``) to
        embed alongside the always-on base UI faces — pass the set a book's
        rendered text actually needs (``src.fonts.scripts_in``) to keep every
        other book's payload from carrying scripts it never prints. ``None``
        (the default) embeds every face, which is what every caller before
        this parameter existed relied on.

        A face with no file on disk raises rather than being silently
        skipped: a declared face that isn't shipped is a packaging bug, and
        skipping it here would just reintroduce the exact system-font
        fallback this method exists to prevent — silently.
        """
        rules = []
        for face in FACES:
            if face.script is not None and scripts is not None and face.script not in scripts:
                continue
            uri = self.asset_data_uri(f"assets/fonts/{face.filename}", "font/woff2")
            if not uri:
                raise FileNotFoundError(
                    f"declared font face {face.filename!r} (family {face.family!r}) "
                    f"is missing from {self.template_dir / 'assets' / 'fonts'}"
                )
            rules.append(
                "@font-face {\n"
                f"  font-family: '{face.family}';\n"
                "  font-style: normal;\n"
                f"  font-weight: {face.weight};\n"
                "  font-display: block;\n"
                f"  src: url({uri}) format('woff2');\n"
                f"  unicode-range: {face.unicode_range};\n"
                "}"
            )
        return "\n".join(rules)


#: Suffixes that mark a value as trusted markup rather than text to escape.
_MARKUP_KEYS = ("body", "art", "items", "rows", "options", "cards", "panels",
                "prompts", "stars", "lines", "left", "right", "pages", "contents", "css",
                "cells", "words", "across", "down", "logo_html", "fonts",
                "start_endcap", "goal_endcap", "art_html", "nodes",
                "dictionary", "entries")


def _is_markup(key: str) -> bool:
    return key in _MARKUP_KEYS


def esc(value: Any) -> str:
    """Escape a value for safe inclusion in HTML."""
    return html.escape(str(value), quote=True)
