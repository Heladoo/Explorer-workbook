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
class SymbolBrief:
    """One small standalone picture, drawn from its own prompt.

    A page whose working area is a *table* of pictures — the scavenger hunt
    grid — asks for one of these per cell instead of asking a single prompt to
    draw the whole labelled grid. One subject per prompt is what image models
    are reliable at; exact cell counts and in-image checkboxes are not.

    ``key`` is a stable, language-independent slug naming the prompt file and
    the generated image. A symbol whose subject is the same everywhere (a stop
    sign) therefore has the same key in every book, so its drawing can be
    generated once and reused. ``subject`` is always English; ``label`` is what
    the child reads, in the workbook's language.
    """

    key: str
    label: str
    subject: str
    #: Filled by Agent 4 — the activity never writes prompt text itself.
    prompt: str = ""
    #: ``False`` marks a destination-specific sight, whose drawing is only
    #: reusable within books about the same place.
    universal: bool = True
    #: Whether ``sources/symbols/prompts/<key>.md`` actually exists — only
    #: the library's always-findable pool (``ubiquity`` "everywhere"/"common")
    #: has one; a "regional"/"local" ``ready`` symbol got its art some other
    #: way (hand-authored from a destination's doodle sheet, typically) and
    #: was never machine-prompted. Set by the pipeline, which knows the whole
    #: library — a bare ``SymbolBrief`` has no way to check this itself.
    has_shared_prompt: bool = False

    @property
    def prompt_filename(self) -> str:
        """Prompt path relative to ``prompts/``, e.g. ``symbols/stop-sign.md``."""
        return f"symbols/{self.key}.md"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "subject": self.subject,
            "prompt": self.prompt,
            "universal": self.universal,
        }
        # This symbol has no per-book prompt file — see ``prompt`` above —
        # so ``prompt_file`` must name the one place a real prompt actually
        # lives, and only when it does. Claiming the per-book path here was
        # always false (nothing ever writes prompts/symbols/*.md), and
        # claiming the shared path unconditionally would be false for every
        # "regional"/"local" symbol too — see ``has_shared_prompt`` above.
        if self.has_shared_prompt:
            data["prompt_file"] = f"sources/symbols/prompts/{self.key}.md"
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
    image_brief: ImageBrief | None = None
    educational_goal: str = ""
    estimated_age: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    #: Per-cell pictures for pages that lay their artwork out as a table.
    symbols: tuple[SymbolBrief, ...] = ()

    def to_page(
        self,
        number: int,
        image_prompt: str,
        symbols: tuple[SymbolBrief, ...] | None = None,
        span: int = 1,
    ) -> "Page":
        """Combine the draft with its page number and rendered prompts."""
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
            symbols=tuple(symbols if symbols is not None else self.symbols),
            span=span,
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
    #: Per-cell pictures, each with its own prompt. Empty for most pages.
    symbols: tuple[SymbolBrief, ...] = ()
    #: How many page slots this page occupies. ``2`` marks a double-page
    #: centre spread — one physical sheet side, printed as one landscape PDF
    #: page, that the reader sees as the two facing pages ``number`` and
    #: ``number + 1``. Everything downstream counts slots rather than
    #: ``len(pages)`` because of this; see ``Workbook.page_count``.
    span: int = 1

    @property
    def is_spread(self) -> bool:
        return self.span > 1

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
        data: dict[str, Any] = {
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
        if self.span != 1:
            data["span"] = self.span
        if self.symbols:
            data["symbols"] = [symbol.to_dict() for symbol in self.symbols]
        return data


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
