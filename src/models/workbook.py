"""The finished workbook: an ordered set of pages plus provenance metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.models.page import Page


@dataclass(frozen=True)
class Workbook:
    """The complete workbook description serialized to ``workbook.json``."""

    title: str
    destination: str
    pages: tuple[Page, ...] = ()
    language: str = "en"
    generated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "pages", tuple(self.pages))

    @property
    def page_count(self) -> int:
        """How many page slots the book has, which is what the reader counts.

        Not ``len(self.pages)``: a double-page centre spread is one :class:`Page`
        occupying two slots (see ``Page.span``), so a 12-page book containing a
        spread holds 11 ``Page`` objects. ``page_count`` is the number that has
        to stay a multiple of 4 for the booklet to fold, so it is the one that
        counts slots.
        """
        return sum(page.span for page in self.pages)

    @property
    def sheet_count(self) -> int:
        """Physical pages in the rendered PDF — one per :class:`Page`."""
        return len(self.pages)

    @property
    def activity_types(self) -> tuple[str, ...]:
        return tuple(page.type for page in self.pages)

    def page_by_type(self, activity_type: str) -> Page | None:
        for page in self.pages:
            if page.type == activity_type:
                return page
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "destination": self.destination,
            "language": self.language,
            "generated_at": self.generated_at,
            "page_count": self.page_count,
            "pages": [page.to_dict() for page in self.pages],
            "metadata": dict(self.metadata),
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize to JSON. ``ensure_ascii`` is off so non-Latin copy stays readable."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False) + "\n"
