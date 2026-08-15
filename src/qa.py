"""Post-generation QA: catch English text that leaked into a Hebrew (or any
non-English) workbook.

The destination's canonical name and the children's names are allowed to stay
Latin script by design (see ``CLAUDE.md``); the prompt language always stays
English separately and is never scanned here. Everything else a page shows
the reader — title, instructions, checklist items, quiz questions, card
captions, and so on — should be written in the workbook's own language.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from src.models.context import WorkbookContext
from src.models.page import Page
from src.models.workbook import Workbook

_LATIN_WORD = re.compile(r"[A-Za-z]{2,}")

#: Metadata keys that are internal bookkeeping, not reader-facing text — a
#: destination slug, an enum, a coordinate, a count — so they're never scanned.
_SKIP_KEYS = frozenset(
    {
        "difficulty", "focus", "itinerary_day", "grid", "grid_size", "layout",
        "rows", "cols", "columns", "numbers", "direction", "row", "column",
        "placements", "solution", "needs_illustration", "illustration",
        "blank_slots", "matched_conditions", "item_count", "object_count",
        "pair_count", "question_count", "difference_count", "clue_count",
        "star_rating", "stars", "writing_lines", "closing_page", "blank_page",
        "title_placeholder", "name_line", "personalized", "subject_kind",
        "knowledge_focus", "answer_key", "start", "goal", "kind",
        "answer_index", "length", "number", "child_names", "seed",
        "schema_version", "request", "plan", "knowledge_source",
        "prompt_language", "requested_language", "category", "source",
        "notes",
        # Symbol slugs are deliberately English in every language: they name a
        # prompt file and an image cache entry, and are the reason one drawing
        # can be shared between a Hebrew and an English book. The reader-facing
        # labels live in ``items`` / ``left_column`` and *are* scanned.
        # ``shadow_keys`` is the matching page's second column, in the same
        # slugs, so the layout can pair a drawing with its shadow without
        # going through a translated label. The packing page's equivalents:
        # ``backpack_key`` names the hub symbol, ``ring_keys`` is print order
        # around it, ``pack_keys``/``distractor_keys`` split that same ring
        # for the answer key — all slugs, none of them reader-facing (the
        # translated labels live in ``items`` / ``not_to_pack``).
        "symbol_keys", "shadow_keys",
        "backpack_key", "ring_keys", "pack_keys", "distractor_keys",
        # The quiz's dictionary section (src/activities/quiz.py,
        # src/phrasebook.py): "native" is the destination-language word,
        # deliberately in a *different* script from the workbook by design
        # — a Czech word inside a Hebrew book is correct there, not a leak,
        # exactly like a symbol slug. "concept" and "country" are internal
        # tokens (a fixed phrasebook key, an ISO country code); "script" and
        # "native_language"/"native_direction" are font/layout bookkeeping.
        # "pronunciation" is deliberately *not* here: it must always be
        # written in the workbook's own script, so a Latin pronunciation in
        # a Hebrew book is a real leak this scanner should keep catching.
        "native", "concept", "country", "script",
        "native_language", "native_direction",
    }
)


@dataclass(frozen=True)
class LeakFinding:
    """One place a Latin word turned up where it shouldn't have."""

    page_number: int
    page_type: str
    field: str
    words: tuple[str, ...]
    text: str

    def __str__(self) -> str:
        return (
            f"page {self.page_number} ({self.page_type}) {self.field}: "
            f"{', '.join(self.words)} — {self.text!r}"
        )


def find_english_leaks(
    workbook: Workbook, context: WorkbookContext | None = None
) -> list[LeakFinding]:
    """Scan every page's reader-facing text for stray Latin-script words.

    Returns an empty list for an English workbook (nothing to leak) or a
    clean translation. Non-empty results are not necessarily bugs — a
    destination with no translated data pack will legitimately show its
    English facts — but they are exactly what to check after generating or
    editing a Hebrew workbook.
    """
    if workbook.language == "en":
        return []

    allowed = _allowed_words(workbook, context)
    findings: list[LeakFinding] = []
    for page in workbook.pages:
        findings.extend(_scan_page(page, allowed))
    return findings


def _allowed_words(workbook: Workbook, context: WorkbookContext | None) -> set[str]:
    names = [workbook.destination]
    if context is not None:
        names.append(context.destination)
        names.extend(context.child_names)
    allowed: set[str] = set()
    for name in names:
        allowed.update(word.upper() for word in _LATIN_WORD.findall(name))
    return allowed


def _scan_page(page: Page, allowed: set[str]) -> list[LeakFinding]:
    # `educational_goal` is internal build documentation (see CLAUDE.md /
    # src/activities/base.py) — a fixed English class attribute, never shown
    # to the reader and never templated through the locale, so it is not
    # part of this scan.
    findings: list[LeakFinding] = []
    for field_name, value in (
        ("title", page.title),
        ("instructions", page.instructions),
    ):
        findings.extend(_check_text(page, field_name, value, allowed))
    for key, value in page.metadata.items():
        if key in _SKIP_KEYS:
            continue
        for text in _collect_texts(value, _SKIP_KEYS):
            findings.extend(_check_text(page, f"metadata.{key}", text, allowed))
    return findings


def _collect_texts(value: Any, skip_keys: frozenset) -> list[str]:
    if isinstance(value, dict):
        texts = []
        for key, item in value.items():
            if key in skip_keys:
                continue
            texts.extend(_collect_texts(item, skip_keys))
        return texts
    if isinstance(value, (list, tuple)):
        texts = []
        for item in value:
            texts.extend(_collect_texts(item, skip_keys))
        return texts
    if isinstance(value, str):
        return [value]
    return []


def _check_text(page: Page, field_name: str, text: str, allowed: set[str]) -> list[LeakFinding]:
    if not text:
        return []
    leaked = tuple(
        word for word in _LATIN_WORD.findall(text) if word.upper() not in allowed
    )
    if not leaked:
        return []
    return [LeakFinding(page.number, page.type, field_name, leaked, text)]


def format_report(findings: list[LeakFinding]) -> str:
    """A short, human-readable summary for the CLI/web form to print."""
    if not findings:
        return "Hebrew QA: no stray English found."
    lines = [f"Hebrew QA: {len(findings)} possible English leak(s):"]
    lines.extend(f"  - {finding}" for finding in findings)
    return "\n".join(lines)


__all__ = ["LeakFinding", "find_english_leaks", "format_report"]
