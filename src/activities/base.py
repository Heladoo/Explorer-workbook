"""The activity plugin contract and its registry.

Adding a new activity means adding one module to :mod:`src.activities` with a
``@register_activity`` decorated class. Nothing else in the codebase changes:
the package auto-discovers modules and the planner picks up whatever it finds.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Type

from src.models.context import WorkbookContext
from src.models.page import ActivityDraft, ImageBrief, RenderMode, SymbolBrief
from src.models.plan import PlannedPage
from src.strings import Strings, strings_for


#: Knowledge categories whose entries name something you can draw. ``history``
#: and ``interesting_facts`` hold sentences, so they never become a page subject.
VISUAL_CATEGORIES = ("landmarks", "wildlife", "plants", "activities", "local_food")

#: The subset whose entries are noun phrases, so they read correctly inside a
#: title or a sentence ("Color the camel yard", not "Color riding a camel").
NOUN_CATEGORIES = ("landmarks", "wildlife", "plants")


class ActivityGenerator(ABC):
    """Base class for every activity.

    Subclasses declare who the activity is for and what it teaches, then
    implement :meth:`generate`. They read from the shared context only — an
    activity must never call another activity or touch the filesystem.
    """

    #: Stable identifier used in ``workbook.json``, prompt filenames and plans.
    activity_type: str = ""
    #: Title shown in documentation when the activity has no dynamic title.
    display_name: str = ""
    #: What the child practises on this page.
    educational_goal: str = ""
    #: Age range the activity is suitable for.
    min_age: int = 3
    max_age: int = 12
    #: Planner hints. ``weight`` biases selection, ``max_per_workbook`` caps
    #: repeats, ``pinned`` places the page at a fixed position (1 = first,
    #: -1 = last), and ``energy`` lets the planner alternate quiet/active pages.
    #: ``enabled`` is a hard gate: ``False`` removes the activity from the
    #: planner's default catalogue entirely (it never fills a body slot, even
    #: as a last-resort repeat) while leaving it registered and generatable —
    #: a paused activity, not a deleted one. A caller that explicitly injects
    #: an activity list into ``WorkbookPlanner`` bypasses this gate, since
    #: that's an explicit request for exactly those activities.
    weight: int = 10
    max_per_workbook: int = 1
    pinned: int | None = None
    energy: str = "calm"
    enabled: bool = True
    #: ``True`` asks for the double-page centre spread: one landscape page the
    #: reader sees as the two facing pages at the exact middle of the booklet.
    #:
    #: A *request*, not a requirement. The centre spread only exists in a
    #: folded format whose page count actually has a centre (see
    #: ``PageFormat.allows_spread`` and the planner), so an activity marked
    #: this way still has to work as an ordinary single page — in the A4
    #: format it simply competes for a body slot like anything else.
    spread: bool = False
    #: Knowledge categories the activity needs; used by :meth:`supports`.
    required_knowledge: tuple[str, ...] = ()

    def supports(self, context: WorkbookContext) -> bool:
        """Whether this activity can produce a good page for this context.

        The default checks the child's age against the declared range and that
        every required knowledge category has at least one entry.
        """
        if context.max_age < self.min_age or context.min_age > self.max_age:
            return False
        return all(context.knowledge.get(name) for name in self.required_knowledge)

    @abstractmethod
    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        """Produce the page content for this slot."""

    # -- helpers available to every subclass -----------------------------

    def draft(
        self,
        *,
        title: str,
        instructions: str,
        planned: PlannedPage,
        image_brief: ImageBrief | None = None,
        metadata: dict[str, Any] | None = None,
        educational_goal: str | None = None,
        symbols: tuple[SymbolBrief, ...] = (),
    ) -> ActivityDraft:
        """Assemble a draft, filling in the boilerplate fields consistently.

        ``symbols`` is for pages whose working area is a *table of pictures*:
        each one is drawn from its own small prompt and placed by the layout,
        rather than asking a single prompt to draw the whole grid.
        """
        page_metadata: dict[str, Any] = {
            "difficulty": planned.difficulty,
            "focus": planned.focus,
        }
        if planned.itinerary_day:
            page_metadata["itinerary_day"] = planned.itinerary_day
        page_metadata.update(metadata or {})
        return ActivityDraft(
            type=self.activity_type,
            title=title,
            instructions=instructions,
            image_brief=image_brief,
            educational_goal=educational_goal or self.educational_goal,
            estimated_age=self.estimated_age(planned),
            metadata=page_metadata,
            symbols=tuple(symbols),
        )

    def estimated_age(self, planned: PlannedPage) -> str:
        """Age recommendation for this page, clamped to the activity's range."""
        low = max(self.min_age, planned.target_age - 1)
        high = min(self.max_age, max(low, planned.target_age + 1))
        return f"{low}-{high}"

    def pick(
        self,
        context: WorkbookContext,
        category: str,
        count: int,
        *,
        fallback: Iterable[str] = (),
        salt: object = "",
    ) -> tuple[str, ...]:
        """Deterministically sample ``count`` entries from a knowledge category.

        Pass ``salt`` (usually the page number) when an activity can appear more
        than once in a book, so the second page doesn't repeat the first's picks.
        """
        values = context.knowledge.get(category) or tuple(fallback)
        return context.sample(values, count, key=f"{self.activity_type}:{category}:{salt}")

    def visual_focus(
        self,
        planned: PlannedPage,
        default: str = "landmarks",
        allowed: tuple[str, ...] = VISUAL_CATEGORIES,
    ) -> str:
        """The planner's focus, when it names something this page can draw."""
        if planned.focus in allowed:
            return planned.focus
        return default

    def strings(self, context: WorkbookContext) -> Strings:
        """Copy for the workbook's language."""
        return strings_for(context.language)

    def text(self, context: WorkbookContext, key: str, **kwargs: Any) -> str:
        """Shorthand for ``self.strings(context).text(key, ...)``."""
        return strings_for(context.language).text(key, **kwargs)

    def hero(self, context: WorkbookContext) -> str:
        """The child the page addresses, or a neutral stand-in."""
        names = context.child_names
        if not names:
            return self.text(context, "common.explorer")
        return names[context.rng_for(f"{self.activity_type}:hero").randrange(len(names))]


#: Registry of every discovered activity, keyed by ``activity_type``.
ACTIVITY_REGISTRY: dict[str, Type[ActivityGenerator]] = {}


def register_activity(cls: Type[ActivityGenerator]) -> Type[ActivityGenerator]:
    """Class decorator that adds an activity to the registry."""
    activity_type = getattr(cls, "activity_type", "")
    if not activity_type:
        raise ValueError(f"{cls.__name__} must define a non-empty activity_type")
    existing = ACTIVITY_REGISTRY.get(activity_type)
    if existing is not None and existing is not cls:
        raise ValueError(
            f"duplicate activity_type {activity_type!r}: "
            f"{existing.__name__} and {cls.__name__}"
        )
    ACTIVITY_REGISTRY[activity_type] = cls
    return cls


def get_generator(activity_type: str) -> ActivityGenerator:
    """Instantiate the generator registered for ``activity_type``."""
    try:
        cls = ACTIVITY_REGISTRY[activity_type]
    except KeyError as exc:
        known = ", ".join(sorted(ACTIVITY_REGISTRY)) or "<none>"
        raise KeyError(f"unknown activity type {activity_type!r}; known: {known}") from exc
    return cls()


def available_activities() -> tuple[ActivityGenerator, ...]:
    """Instantiate every registered activity, in a stable order."""
    return tuple(cls() for _, cls in sorted(ACTIVITY_REGISTRY.items()))


__all__ = [
    "ACTIVITY_REGISTRY",
    "ActivityGenerator",
    "ImageBrief",
    "PlannedPage",
    "RenderMode",
    "SymbolBrief",
    "available_activities",
    "get_generator",
    "register_activity",
]
