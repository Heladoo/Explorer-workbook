"""Agent 4 — Prompt Generator.

The only component that knows how an image prompt is worded. Activities hand
it a structured :class:`~src.models.page.ImageBrief`; it applies the book-wide
style contract and returns text that can be pasted straight into GPT Image,
DALL-E, Midjourney or Flux.

Prompts are written in English regardless of the workbook language, because
that is what image models are trained on. The workbook metadata records this.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from string import Template

from src.models.context import WorkbookContext
from src.models.page import ImageBrief, RenderMode

DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"

#: Opening sentence per render mode — sets the deliverable before anything else.
_OPENINGS: dict[str, str] = {
    RenderMode.COLORING: "Create a black-and-white coloring page for a children's travel activity book.",
    RenderMode.PUZZLE: "Create a black-and-white puzzle illustration for a children's travel activity book.",
    RenderMode.ILLUSTRATION: "Create a black-and-white illustrated information page for a children's travel activity book.",
    RenderMode.FRAME: "Create a black-and-white activity page with a large empty drawing area for a children's travel activity book.",
}

#: The line-work rule per render mode.
_MODE_STYLES: dict[str, str] = {
    RenderMode.COLORING: (
        "Bold, clean, uniform black outlines on white with large open areas to color — "
        "no shading, no hatching, no grey fills, no solid black areas"
    ),
    RenderMode.PUZZLE: (
        "Crisp black line art with high contrast and clear separation between elements, so "
        "the puzzle stays readable when printed small — no shading or textures that could "
        "be mistaken for part of the puzzle"
    ),
    RenderMode.ILLUSTRATION: (
        "Accurate black line art with light grey shading used sparingly for depth, keeping "
        "every subject clearly identifiable"
    ),
    RenderMode.FRAME: (
        "Delicate black line art confined to the border, with the working area left "
        "completely blank white"
    ),
}


@dataclass(frozen=True)
class StyleGuide:
    """The book-wide look, injected so a different house style is a different object."""

    signature: str = (
        "same line weight, same simple horizon treatment and the same friendly "
        "character design on every page"
    )
    openings: dict[str, str] = field(default_factory=lambda: dict(_OPENINGS))
    mode_styles: dict[str, str] = field(default_factory=lambda: dict(_MODE_STYLES))

    def opening(self, render_mode: str) -> str:
        return self.openings.get(render_mode, self.openings[RenderMode.COLORING])

    def mode_style(self, render_mode: str) -> str:
        return self.mode_styles.get(render_mode, self.mode_styles[RenderMode.COLORING])


class PromptGenerator:
    """Renders an :class:`ImageBrief` into a finished image-model prompt."""

    def __init__(
        self,
        style: StyleGuide | None = None,
        *,
        template_dir: Path | str | None = None,
    ) -> None:
        self.style = style or StyleGuide()
        self.template_dir = Path(template_dir) if template_dir else DEFAULT_TEMPLATE_DIR
        self._style_template = Template(
            (self.template_dir / "style_guide.tmpl").read_text(encoding="utf-8")
        )

    def render(self, brief: ImageBrief, context: WorkbookContext) -> str:
        """Return the full prompt for one page."""
        if brief.prompt_override:
            return brief.prompt_override.strip() + "\n"

        sections: list[str] = [self.style.opening(brief.render_mode)]

        scene = brief.scene or brief.subject
        sections.append(f"Scene:\n{scene}")

        if brief.elements:
            bullets = "\n".join(f"• {element}" for element in brief.elements)
            sections.append(f"Include:\n{bullets}")

        if brief.composition:
            sections.append(f"Layout:\n{brief.composition}")

        sections.append(self._style_block(brief, context))

        return "\n\n".join(section.strip() for section in sections) + "\n"

    def prompt_file(self, prompt: str) -> str:
        """The body of ``prompts/NN_type.md`` — the prompt and nothing else."""
        return prompt if prompt.endswith("\n") else prompt + "\n"

    # -- internals -------------------------------------------------------

    def _style_block(self, brief: ImageBrief, context: WorkbookContext) -> str:
        extra = "".join(f"\n• {constraint}" for constraint in brief.extra_constraints)
        return self._style_template.substitute(
            mode_style=self.style.mode_style(brief.render_mode),
            age_band=context.age_band,
            style_signature=self._signature(context),
            characters=self._characters(context),
            extra_constraints=extra,
        ).rstrip()

    def _signature(self, context: WorkbookContext) -> str:
        return f"a single coherent book about {context.destination}, {self.style.signature}"

    def _characters(self, context: WorkbookContext) -> str:
        """A recurring cast description, so the same kids appear on every page."""
        if not context.children:
            return ""
        ages = [child.age for child in context.children if child.age is not None]
        if ages:
            age_phrase = " and ".join(f"about {age}" for age in sorted(ages))
            who = f"{_count_word(len(context.children))} child explorers, {age_phrase} years old"
        else:
            who = f"{_count_word(len(context.children))} child explorers"
        return (
            f"\n• Recurring characters, drawn identically wherever they appear: {who}, "
            "with simple round friendly faces, practical outdoor clothes and small backpacks"
        )


def _count_word(count: int) -> str:
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
    return words.get(count, str(count))
