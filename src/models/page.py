"""Page-level models: what an activity produces and what ends up in the book.

An activity generator returns an :class:`ActivityDraft` containing a structured
:class:`ImageBrief` — *not* a finished prompt string. Agent 4 (the prompt
generator) is the only component that knows how prompts are worded, so the
illustration style can be changed in one place without touching any activity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


class RenderMode:
    """How an illustration should be drawn.

    Chosen by the activity, honoured by the prompt generator. Kept as plain
    string constants so a new activity can introduce a new mode without an
    enum migration.
    """

    #: Pure black-and-white outlines, meant to be coloured in by the child.
    COLORING = "coloring"
    #: Black-and-white line art that must stay readable as a puzzle.
    PUZZLE = "puzzle"
    #: Light grey shading allowed; used for fact and reference illustrations.
    ILLUSTRATION = "illustration"
    #: Mostly empty page with a decorated frame for the child to draw in.
    FRAME = "frame"

    ALL = (COLORING, PUZZLE, ILLUSTRATION, FRAME)


@dataclass(frozen=True)
class ImageBrief:
    """A structured description of the illustration a page needs.

    ``prompt_override`` is an escape hatch: an activity that genuinely needs
    full control over its prompt can set it, and the prompt generator will use
    it verbatim instead of rendering the brief.
    """

    subject: str
    scene: str = ""
    elements: tuple[str, ...] = ()
    render_mode: str = RenderMode.COLORING
    composition: str = ""
    extra_constraints: tuple[str, ...] = ()
    prompt_override: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "elements", _clean(self.elements))
        object.__setattr__(self, "extra_constraints", _clean(self.extra_constraints))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "subject": self.subject,
            "scene": self.scene,
            "elements": list(self.elements),
            "render_mode": self.render_mode,
        }
        if self.composition:
            data["composition"] = self.composition
        if self.extra_constraints:
            data["extra_constraints"] = list(self.extra_constraints)
        return data


@dataclass(frozen=True)
class ActivityDraft:
    """What an activity generator returns.

    The draft is deliberately free of page numbers and prompt text: the
    pipeline assigns the former and Agent 4 produces the latter.
    """

    type: str
    title: str
    instructions: str
    image_brief: ImageBrief
    educational_goal: str = ""
    estimated_age: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_page(self, number: int, image_prompt: str) -> "Page":
        """Combine the draft with its page number and rendered prompt."""
        return Page(
            number=number,
            type=self.type,
            title=self.title,
            instructions=self.instructions,
            image_prompt=image_prompt,
            educational_goal=self.educational_goal,
            estimated_age=self.estimated_age,
            metadata=dict(self.metadata),
            image_brief=self.image_brief,
        )


@dataclass(frozen=True)
class Page:
    """A single finished workbook page, as serialized into ``workbook.json``."""

    number: int
    type: str
    title: str
    instructions: str
    image_prompt: str
    educational_goal: str = ""
    estimated_age: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    image_brief: ImageBrief | None = None

    @property
    def prompt_filename(self) -> str:
        """Stable filename for this page's prompt, e.g. ``03_maze.md``."""
        return f"{self.number:02d}_{self.type}.md"

    @property
    def illustration_summary(self) -> str:
        """One-line description of the required illustration, for the docs."""
        if self.image_brief is None:
            return ""
        brief = self.image_brief
        parts = [brief.subject]
        if brief.scene:
            parts.append(brief.scene)
        return " — ".join(part for part in parts if part)

    def to_dict(self) -> dict[str, Any]:
        metadata = dict(self.metadata)
        if self.image_brief is not None:
            metadata.setdefault("image_brief", self.image_brief.to_dict())
        return {
            "number": self.number,
            "type": self.type,
            "title": self.title,
            "instructions": self.instructions,
            "image_prompt": self.image_prompt,
            "educational_goal": self.educational_goal,
            "estimated_age": self.estimated_age,
            "prompt_file": f"prompts/{self.prompt_filename}",
            "metadata": metadata,
        }


def _clean(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    seen: dict[str, None] = {}
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            seen.setdefault(text, None)
    return tuple(seen)
