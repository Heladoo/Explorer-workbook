"""Prints the workbook to a real A4 PDF.

Implements :class:`src.ports.DocumentRenderer`. The layout itself lives in the
HTML templates under ``src/templates/pdf/``; this module only drives a
headless Chromium to print them.

Playwright is an optional dependency: everything else in the project, HTML
layout included, works without it.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from src.models.context import WorkbookContext
from src.models.workbook import Workbook
from src.rendering.html_renderer import HtmlRenderer

logger = logging.getLogger(__name__)

INSTALL_HINT = (
    "PDF rendering needs Playwright: pip install playwright "
    "(a Chromium build must be available; set CHROMIUM_EXECUTABLE if it lives "
    "somewhere unusual)."
)

#: Where Chromium builds are commonly unpacked, newest last.
_CHROMIUM_GLOBS = (
    "chromium-*/chrome-linux/chrome",
    "chromium_headless_shell-*/chrome-linux/chrome-headless-shell",
    "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    "chromium-*/chrome-win/chrome.exe",
)


class PdfRenderer:
    """Workbook → printable PDF, via the HTML layout and headless Chromium."""

    name = "pdf"

    def __init__(
        self,
        html_renderer: HtmlRenderer | None = None,
        *,
        executable_path: str | None = None,
        keep_html: bool = True,
    ) -> None:
        self.html_renderer = html_renderer or HtmlRenderer()
        self.executable_path = executable_path
        self.keep_html = keep_html

    def render(
        self,
        workbook: Workbook,
        context: WorkbookContext,
        *,
        images: dict[int, Path] | None = None,
        output_path: Path | str,
    ) -> Path:
        """Write the PDF and return its path."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        html = self.html_renderer.render(workbook, context, images=images)

        if self.keep_html:
            source = target.with_suffix(".html")
            source.write_text(html, encoding="utf-8")
            self._print(source, target)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "workbook.html"
                source.write_text(html, encoding="utf-8")
                self._print(source, target)
        return target

    # -- internals -------------------------------------------------------

    def _print(self, source: Path, target: Path) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - depends on the environment
            raise RuntimeError(INSTALL_HINT) from exc

        with sync_playwright() as playwright:
            browser = self._launch(playwright)
            try:
                page = browser.new_page()
                page.goto(source.resolve().as_uri(), wait_until="load")
                page.pdf(
                    path=str(target),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()

    def _launch(self, playwright):
        """Launch Chromium, coping with a browser installed out of band."""
        discovered = self.executable_path or find_chromium()
        attempts = []
        if discovered:
            attempts.append({"executable_path": discovered})
        attempts.append({})
        if discovered:
            attempts.append({"executable_path": discovered, "args": ["--no-sandbox"]})

        last_error: Exception | None = None
        for options in attempts:
            try:
                return playwright.chromium.launch(**options)
            except Exception as exc:  # try the next strategy
                last_error = exc
                logger.debug("chromium launch failed with %s: %s", options, exc)
        raise RuntimeError(f"could not start Chromium for PDF rendering. {INSTALL_HINT}") from last_error


def find_chromium() -> str | None:
    """Locate a Chromium binary without downloading anything."""
    explicit = os.environ.get("CHROMIUM_EXECUTABLE")
    if explicit and Path(explicit).exists():
        return explicit

    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not root:
        return None
    base = Path(root)
    if not base.is_dir():
        return None
    for pattern in _CHROMIUM_GLOBS:
        matches = sorted(path for path in base.glob(pattern) if path.exists())
        if matches:
            return str(matches[-1])
    return None
