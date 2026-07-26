"""Layout stage: workbook structure → printable document.

Separate from the generators by design — no activity knows a page size, and
this package adds no content, it only arranges what ``workbook.json`` already
describes.
"""

from src.rendering.html_renderer import HtmlRenderer
from src.rendering.layouts import LAYOUTS, LayoutContext, build_body, layout
from src.rendering.pdf_renderer import PdfRenderer, find_chromium
from src.rendering.templates import TemplateSet

__all__ = [
    "LAYOUTS",
    "HtmlRenderer",
    "LayoutContext",
    "PdfRenderer",
    "TemplateSet",
    "build_body",
    "find_chromium",
    "layout",
]
