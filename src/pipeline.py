"""Wires the five agents together.

The builder owns the data flow and nothing else: knowledge in, plan, drafts,
prompts, documents out. Every collaborator is injected, so a different
knowledge source, planner or house style is a constructor argument rather than
an edit.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Callable, Sequence

from src import decor
from src.activities import load_activities
from src.activities.base import VISUAL_CATEGORIES, get_generator
from src.agents.destination_agent import DestinationKnowledgeAgent, build_knowledge_agent
from src.agents.markdown_generator import MarkdownGenerator
from src.agents.planner import WorkbookPlanner
from src.agents.prompt_generator import PromptGenerator
from src.models.context import Child, Trip, WorkbookContext
from src.models.page import Page
from src.models.plan import PlannedPage
from src.models.workbook import Workbook
from src.rendering.formats import get_format
from src.strings import strings_for
from src.symbols import library

#: Bumped when the output shape changes, so downstream tools can adapt.
SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class WorkbookRequest:
    """Everything the caller can ask for. Only ``destination`` is required."""

    destination: str
    children: Sequence[str] = ()
    ages: Sequence[int] = ()
    language: str = "en"
    page_count: int = 12
    difficulty: str | None = None
    theme: str | None = None
    interests: Sequence[str] = ()
    itinerary: Sequence[str] = ()
    duration_days: int | None = None
    start_date: str | None = None
    family_photos: Sequence[str] = ()
    seed: int = 0
    #: See ``WorkbookContext.page_format``.
    page_format: str = "a5-booklet"

    def to_context(self) -> WorkbookContext:
        """Build the shared context, pairing each child with their age by position."""
        if not self.destination or not self.destination.strip():
            raise ValueError("destination is required")
        ages = list(self.ages)
        children = tuple(
            Child(name=name, age=ages[index] if index < len(ages) else None)
            for index, name in enumerate(self.children)
        )
        if len(ages) > len(children):
            raise ValueError(
                f"got {len(ages)} ages for {len(children)} children — "
                "pass one age per child, in the same order"
            )
        return WorkbookContext(
            destination=self.destination.strip(),
            children=children,
            trip=Trip(
                itinerary=tuple(self.itinerary),
                duration_days=self.duration_days,
                start_date=self.start_date,
            ),
            theme=self.theme,
            language=self.language,
            page_count=self.page_count,
            difficulty=self.difficulty,
            interests=tuple(self.interests),
            family_photos=tuple(self.family_photos),
            seed=self.seed,
            # Validated here rather than at the CLI alone, so the API and the
            # web form get the same error instead of an unknown key silently
            # meaning "no centre spread" three layers down.
            page_format=get_format(self.page_format).key,
        )


@dataclass(frozen=True)
class WorkbookBundle:
    """The three artifacts, in memory. Writing them to disk is a separate step."""

    workbook: Workbook
    markdown: str
    prompts: dict[str, str] = field(default_factory=dict)
    context: WorkbookContext | None = None
    plan: tuple[PlannedPage, ...] = ()

    @property
    def json(self) -> str:
        return self.workbook.to_json()


class WorkbookBuilder:
    """Agent 1 → 2 → 3 → 4 → 5, in that order, with nothing skipping ahead."""

    def __init__(
        self,
        knowledge_agent: DestinationKnowledgeAgent | None = None,
        planner: WorkbookPlanner | None = None,
        prompt_generator: PromptGenerator | None = None,
        markdown_generator: MarkdownGenerator | None = None,
        *,
        clock: Callable[[], str] | None = None,
    ) -> None:
        load_activities()
        self.knowledge_agent = knowledge_agent or build_knowledge_agent("auto")
        self.planner = planner or WorkbookPlanner()
        self.prompt_generator = prompt_generator or PromptGenerator()
        self.markdown_generator = markdown_generator or MarkdownGenerator()
        self.clock = clock or _utc_now

    def build(self, request: WorkbookRequest) -> WorkbookBundle:
        context = request.to_context()

        # Agent 1 — destination knowledge.
        knowledge = self.knowledge_agent.fetch(
            context.destination,
            interests=context.interests,
            language=strings_for(context.language).language,
        )
        context = context.with_knowledge(knowledge)

        # Agent 2 — plan the pages.
        plan = self.planner.plan(context)

        # Agents 3 and 4 — content, then prompts. Only cover and coloring pages
        # get a page-level illustration prompt; every other activity typesets
        # its own working area and carries no image of its own (see each
        # activity's ``needs_illustration: False`` metadata). Symbols (the
        # small per-cell pictures scavenger hunts, matching and packing pages
        # use) are drawn from the shared, checked-in `sources/symbols/` cache
        # rather than a fresh prompt per book — see the doodle/grid prompt
        # below for how new ones get sourced.
        # The only symbols with a real, checked-in prompt (as opposed to
        # committed art with no machine prompt behind it — see
        # ``SymbolBrief.has_shared_prompt``) are the library's always-findable
        # pool. Computed once per book; ``library()`` itself is cached.
        prompt_available_keys = frozenset(symbol.key for symbol in library().universal_pool())

        pages: list[Page] = []
        prompts: dict[str, str] = {}
        for planned in plan:
            generator = get_generator(planned.activity_type)
            draft = generator.generate(context, planned)
            if draft.image_brief is not None:
                prompt = self.prompt_generator.render(draft.image_brief, context)
            else:
                prompt = ""
            symbols = tuple(
                replace(symbol, has_shared_prompt=symbol.key in prompt_available_keys)
                for symbol in draft.symbols
            )
            page = draft.to_page(planned.number, prompt, symbols=symbols, span=planned.span)
            pages.append(page)
            if draft.image_brief is not None:
                prompts[page.prompt_filename] = self.prompt_generator.prompt_file(prompt)

        doodle_grid_prompt = self._doodle_grid_prompt(context)
        if doodle_grid_prompt:
            prompts["doodle_grid.md"] = self.prompt_generator.prompt_file(doodle_grid_prompt)

        workbook = Workbook(
            title=self._title(context),
            destination=context.destination,
            pages=tuple(pages),
            language=strings_for(context.language).language,
            generated_at=self.clock(),
            metadata=self._metadata(context, plan),
        )

        # Agent 5 — documentation.
        markdown = self.markdown_generator.render(workbook, context)

        return WorkbookBundle(
            workbook=workbook,
            markdown=markdown,
            prompts=prompts,
            context=context,
            plan=plan,
        )

    # -- internals -------------------------------------------------------

    def _doodle_grid_prompt(self, context: WorkbookContext) -> str:
        """One sheet of many small local doodles, sourced from the
        destination's own knowledge — not tied to any single page.

        This is deliberately the *only* place a fresh symbol-style drawing
        gets requested per book. The sheet can be printed as-is (it doubles
        as a coloring page), and later split into individual symbol drawings
        with ``tools/split_decor.py`` — see the symbol-authoring skill —
        rather than every book minting its own one-off prompt per icon.

        Skipped once the destination already has a sheet under
        ``sources/Decor/`` — the sheet is a one-time source for that
        destination's symbols, reviewed and registered by hand, not a
        per-book asset to keep re-requesting.
        """
        if decor.existing_doodle(context.destination) is not None:
            return ""
        subjects: list[str] = []
        for category in VISUAL_CATEGORIES:
            subjects.extend(context.sample(context.knowledge.get(category), 4, key=f"doodle_grid:{category}"))
        if not subjects:
            return ""
        return self.prompt_generator.render_doodle_grid(subjects, context)

    def _title(self, context: WorkbookContext) -> str:
        strings = strings_for(context.language)
        names = strings.join(context.child_names)
        if names:
            return strings.text(
                "workbook.title_with_names", names=names, destination=context.display_destination
            )
        return strings.text("workbook.title_plain", destination=context.display_destination)

    def _metadata(
        self, context: WorkbookContext, plan: tuple[PlannedPage, ...]
    ) -> dict[str, object]:
        strings = strings_for(context.language)
        metadata: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "subtitle": strings.text("workbook.subtitle"),
            "knowledge_source": context.knowledge.source,
            "prompt_language": "en",
            "requested_language": context.language,
            "seed": context.seed,
            "request": context.to_dict(),
            "plan": [planned.to_dict() for planned in plan],
        }
        if strings.is_fallback:
            metadata["language_fallback"] = (
                f"{context.language} is not available; used {strings.language}"
            )
        if context.knowledge.notes:
            metadata["knowledge_notes"] = list(context.knowledge.notes)
        if context.family_photos:
            metadata["family_photos"] = list(context.family_photos)
        return metadata


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
