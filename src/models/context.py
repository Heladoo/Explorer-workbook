"""The shared context every agent and activity generator receives.

Nothing in this module knows about a specific destination, activity or output
format. It is pure data plus small derived helpers.
"""

from __future__ import annotations

import hashlib
import random
import re
import unicodedata
from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Sequence

#: Ordered difficulty ladder used by the planner and the activity generators.
DIFFICULTY_LEVELS = ("easy", "medium", "hard")

#: The knowledge categories an Agent 1 provider is expected to fill in.
KNOWLEDGE_FIELDS = (
    "landmarks",
    "wildlife",
    "plants",
    "activities",
    "history",
    "local_food",
    "weather",
    "interesting_facts",
)


def slugify(value: str) -> str:
    """Return a filesystem- and URL-safe slug for ``value``.

    Accents are folded rather than dropped so that "Český Krumlov" becomes
    ``cesky-krumlov`` instead of ``cesk-krumlov``.
    """
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return slug or "destination"


def _as_tuple(values: Iterable[str] | None) -> tuple[str, ...]:
    """Normalize any iterable of strings into a clean, de-duplicated tuple."""
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


@dataclass(frozen=True)
class Child:
    """A child the workbook is being written for."""

    name: str
    age: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "age": self.age}


@dataclass(frozen=True)
class Trip:
    """Optional trip details used to ground activities in the real itinerary."""

    itinerary: tuple[str, ...] = ()
    duration_days: int | None = None
    start_date: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "itinerary", _as_tuple(self.itinerary))

    @property
    def effective_duration_days(self) -> int | None:
        """Trip length, inferred from the itinerary when not given explicitly."""
        if self.duration_days:
            return self.duration_days
        return len(self.itinerary) or None

    def to_dict(self) -> dict[str, Any]:
        return {
            "itinerary": list(self.itinerary),
            "duration_days": self.duration_days,
            "start_date": self.start_date,
        }


@dataclass(frozen=True)
class DestinationKnowledge:
    """Structured facts about a destination, produced by Agent 1.

    Every field is a tuple of short human-readable strings. ``source`` records
    which provider produced the knowledge (``file``, ``llm``, ``heuristic``)
    so downstream output can be honest about where the facts came from.
    """

    landmarks: tuple[str, ...] = ()
    wildlife: tuple[str, ...] = ()
    plants: tuple[str, ...] = ()
    activities: tuple[str, ...] = ()
    history: tuple[str, ...] = ()
    local_food: tuple[str, ...] = ()
    weather: tuple[str, ...] = ()
    interesting_facts: tuple[str, ...] = ()
    source: str = "unknown"
    notes: tuple[str, ...] = ()
    #: The destination's name as the child should read it. A translated pack
    #: sets this; ``destination`` itself stays canonical for slugs and prompts.
    display_name: str = ""
    #: Localized term -> English, for knowledge that is not in English. Image
    #: prompts are always written in English, so the prompt generator maps
    #: terms back through this before rendering. Empty for English packs.
    illustration_terms: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        for name in KNOWLEDGE_FIELDS + ("notes",):
            object.__setattr__(self, name, _as_tuple(getattr(self, name)))
        object.__setattr__(self, "illustration_terms", tuple(self.illustration_terms))

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, source: str = "unknown") -> "DestinationKnowledge":
        """Build knowledge from a loosely-typed mapping, ignoring unknown keys."""
        payload = {name: data.get(name, ()) for name in KNOWLEDGE_FIELDS}
        payload["notes"] = data.get("notes", ())
        payload["source"] = data.get("source", source)
        payload["display_name"] = data.get("display_name", "")
        terms = data.get("illustration_terms") or {}
        payload["illustration_terms"] = tuple(
            (str(term), str(english)) for term, english in dict(terms).items()
        )
        return cls(**payload)

    @property
    def english_terms(self) -> dict[str, str]:
        """Localized term -> English, longest first so substrings don't win."""
        return dict(
            sorted(self.illustration_terms, key=lambda pair: len(pair[0]), reverse=True)
        )

    @property
    def is_empty(self) -> bool:
        return not any(getattr(self, name) for name in KNOWLEDGE_FIELDS)

    def coverage(self) -> int:
        """How many knowledge categories are populated (0-8)."""
        return sum(1 for name in KNOWLEDGE_FIELDS if getattr(self, name))

    def get(self, category: str) -> tuple[str, ...]:
        """Return one knowledge category, or an empty tuple if it is unknown."""
        return tuple(getattr(self, category, ()) or ())

    def filled_with(self, fallback: "DestinationKnowledge") -> "DestinationKnowledge":
        """Return a copy where empty categories are taken from ``fallback``.

        Used to top up a sparse data pack (or a thin LLM answer) without
        discarding the richer, more trustworthy entries it did provide.
        """
        patch: dict[str, Any] = {}
        for name in KNOWLEDGE_FIELDS:
            if not getattr(self, name):
                patch[name] = getattr(fallback, name)
        if not patch:
            return self
        patch["notes"] = self.notes + (f"categories completed from {fallback.source}",)
        return replace(self, **patch)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {name: list(getattr(self, name)) for name in KNOWLEDGE_FIELDS}
        data["source"] = self.source
        if self.notes:
            data["notes"] = list(self.notes)
        if self.illustration_terms:
            data["illustration_terms"] = dict(self.illustration_terms)
        return data


@dataclass(frozen=True)
class WorkbookContext:
    """Everything a generator is allowed to know about the job at hand.

    The context is immutable: generators read from it, they never write to it,
    and they never talk to each other.
    """

    destination: str
    knowledge: DestinationKnowledge = field(default_factory=DestinationKnowledge)
    children: tuple[Child, ...] = ()
    trip: Trip = field(default_factory=Trip)
    theme: str | None = None
    language: str = "en"
    page_count: int = 12
    difficulty: str | None = None
    interests: tuple[str, ...] = ()
    family_photos: tuple[str, ...] = ()
    seed: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "children", tuple(self.children))
        object.__setattr__(self, "interests", _as_tuple(self.interests))
        object.__setattr__(self, "family_photos", _as_tuple(self.family_photos))

    # -- derived helpers -------------------------------------------------

    @property
    def slug(self) -> str:
        return slugify(self.destination)

    @property
    def display_destination(self) -> str:
        """The destination as page copy should say it, translated where known."""
        return self.knowledge.display_name or self.destination

    @property
    def child_names(self) -> tuple[str, ...]:
        return tuple(child.name for child in self.children if child.name)

    @property
    def ages(self) -> tuple[int, ...]:
        return tuple(child.age for child in self.children if child.age is not None)

    @property
    def min_age(self) -> int:
        return min(self.ages) if self.ages else 5

    @property
    def max_age(self) -> int:
        return max(self.ages) if self.ages else 9

    @property
    def age_band(self) -> str:
        """Human-readable age range, e.g. ``"5-7"`` or ``"6"``."""
        if self.min_age == self.max_age:
            return str(self.min_age)
        return f"{self.min_age}-{self.max_age}"

    @property
    def has_children(self) -> bool:
        return bool(self.child_names)

    def child_names_phrase(self, conjunction: str = "and") -> str:
        """Join child names for use in a sentence: ``"Noa and Amit"``."""
        names = self.child_names
        if not names:
            return ""
        if len(names) == 1:
            return names[0]
        return f"{', '.join(names[:-1])} {conjunction} {names[-1]}"

    def has_interest(self, *topics: str) -> bool:
        wanted = {topic.lower() for topic in topics}
        return any(interest.lower() in wanted for interest in self.interests)

    # -- deterministic randomness ---------------------------------------

    def rng_for(self, key: str) -> random.Random:
        """Return a generator-local RNG.

        Seeded from ``(seed, destination, key)`` so that two runs with the same
        inputs produce byte-identical output, while two different activities
        still make independent choices.
        """
        digest = hashlib.sha256(f"{self.seed}:{self.slug}:{key}".encode("utf-8")).digest()
        return random.Random(int.from_bytes(digest[:8], "big"))

    def sample(self, values: Sequence[str], count: int, key: str) -> tuple[str, ...]:
        """Pick up to ``count`` distinct values deterministically.

        Order is stable for a given ``key``; if fewer values exist than
        requested, everything available is returned.
        """
        pool = list(values)
        if not pool:
            return ()
        if count >= len(pool):
            return tuple(pool)
        return tuple(self.rng_for(key).sample(pool, count))

    def with_knowledge(self, knowledge: DestinationKnowledge) -> "WorkbookContext":
        return replace(self, knowledge=knowledge)

    def to_dict(self) -> dict[str, Any]:
        return {
            "destination": self.destination,
            "language": self.language,
            "theme": self.theme,
            "page_count": self.page_count,
            "difficulty": self.difficulty,
            "children": [child.to_dict() for child in self.children],
            "trip": self.trip.to_dict(),
            "interests": list(self.interests),
            "family_photos": list(self.family_photos),
            "seed": self.seed,
        }
