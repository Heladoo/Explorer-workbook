"""Agent 5 — Markdown Generator.

Turns the finished workbook structure into the human-readable build
specification (``workbook.md``). Presentation only: it adds no content and
makes no decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from string import Template

from src.models.context import KNOWLEDGE_FIELDS, WorkbookContext
from src.models.page import Page
from src.models.workbook import Workbook

DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"


class MarkdownGenerator:
    """Renders ``workbook.md`` from a :class:`~src.models.workbook.Workbook`."""

    def __init__(self, template_dir: Path | str | None = None) -> None:
        self.template_dir = Path(template_dir) if template_dir else DEFAULT_TEMPLATE_DIR
        self._document = Template(
            (self.template_dir / "workbook_md.tmpl").read_text(encoding="utf-8")
        )
        self._page = Template(
            (self.template_dir / "workbook_md_page.tmpl").read_text(encoding="utf-8")
        )

    def render(self, workbook: Workbook, context: WorkbookContext) -> str:
        overview = "\n".join(self._overview_row(page) for page in workbook.pages)
        pages = "\n".join(self._render_page(page) for page in workbook.pages)
        return self._document.substitute(
            title=workbook.title,
            subtitle=workbook.metadata.get("subtitle", "An activity book for young explorers"),
            destination=workbook.destination,
            language=self._language(workbook),
            page_count=workbook.page_count,
            children=self._children(context),
            trip=self._trip(context),
            interests=", ".join(context.interests) or "—",
            knowledge_source=context.knowledge.source,
            generated_at=workbook.generated_at or "—",
            notes=self._notes(context),
            overview=overview,
            pages=pages,
            knowledge=self._knowledge(context),
        )

    # -- sections --------------------------------------------------------

    def _overview_row(self, page: Page) -> str:
        goal = _cell(page.educational_goal)
        return (
            f"| {page.number} | {page.type} | {page.metadata.get('difficulty', '—')} "
            f"| {page.estimated_age or '—'} | {goal} | "
            f"[`{page.prompt_filename}`](prompts/{page.prompt_filename}) |"
        )

    def _render_page(self, page: Page) -> str:
        return self._page.substitute(
            number=page.number,
            title=page.title,
            type=page.type,
            goal=page.educational_goal or "—",
            age=page.estimated_age or "—",
            difficulty=page.metadata.get("difficulty", "—"),
            prompt_path=f"prompts/{page.prompt_filename}",
            instructions=page.instructions.replace("\n", "\n> "),
            illustration=self._illustration(page),
            image_prompt=page.image_prompt.rstrip(),
            details=self._details(page),
        )

    def _illustration(self, page: Page) -> str:
        brief = page.image_brief
        if brief is None:
            return "—"
        subject = brief.subject[:1].upper() + brief.subject[1:]
        lines = [f"{subject}."]
        if brief.scene:
            lines.append(brief.scene)
        if brief.elements:
            lines.append("Must contain: " + ", ".join(brief.elements) + ".")
        lines.append(f"Render mode: `{brief.render_mode}`.")
        return "\n".join(lines)

    def _details(self, page: Page) -> str:
        payload = {
            key: value for key, value in page.metadata.items() if key != "image_brief"
        }
        if not payload:
            return ""
        body = json.dumps(payload, indent=2, ensure_ascii=False)
        return (
            "<details>\n<summary>Page data for the layout stage</summary>\n\n"
            f"```json\n{body}\n```\n\n</details>\n"
        )

    def _knowledge(self, context: WorkbookContext) -> str:
        blocks = []
        for name in KNOWLEDGE_FIELDS:
            values = context.knowledge.get(name)
            if not values:
                continue
            label = name.replace("_", " ").title()
            entries = "\n".join(f"- {value}" for value in values)
            blocks.append(f"**{label}**\n\n{entries}")
        if context.knowledge.notes:
            notes = "\n".join(f"- {note}" for note in context.knowledge.notes)
            blocks.append(f"**Notes**\n\n{notes}")
        return "\n\n".join(blocks) if blocks else "_No knowledge recorded._"

    def _notes(self, context: WorkbookContext) -> str:
        notes = []
        if context.knowledge.source == "heuristic":
            notes.append(
                "> **Note:** no curated data pack or model answer was available for this "
                "destination, so the pages use generic travel material. Add a pack under "
                "`data/destinations/` or run with `--provider llm` for destination-specific "
                "content."
            )
        if context.family_photos:
            notes.append(
                "> **Note:** family photos were supplied but the MVP does not place images. "
                f"They are recorded in the page metadata ({len(context.family_photos)} file(s))."
            )
        return "\n\n".join(notes) + "\n\n" if notes else ""

    def _children(self, context: WorkbookContext) -> str:
        if not context.children:
            return "—"
        return ", ".join(
            f"{child.name} ({child.age})" if child.age is not None else child.name
            for child in context.children
        )

    def _trip(self, context: WorkbookContext) -> str:
        trip = context.trip
        parts = []
        if trip.effective_duration_days:
            parts.append(f"{trip.effective_duration_days} day(s)")
        if trip.start_date:
            parts.append(f"from {trip.start_date}")
        if trip.itinerary:
            parts.append("itinerary: " + "; ".join(trip.itinerary))
        return ", ".join(parts) if parts else "—"

    def _language(self, workbook: Workbook) -> str:
        requested = workbook.metadata.get("requested_language")
        if requested and requested != workbook.language:
            return f"{workbook.language} (requested `{requested}`, not available)"
        return workbook.language


def _cell(text: str) -> str:
    """Flatten text so it survives inside a markdown table cell."""
    return text.replace("\n", " ").replace("|", "\\|").strip() or "—"
