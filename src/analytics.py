"""Product analytics for the web form.

Local-first and deliberately dull: events are appended to a JSONL file on the
same machine, there are no third-party beacons, no IP addresses are stored, and
the visitor id is a random value in a first-party cookie. ``AnalyticsSink`` is a
Protocol, so pointing this at a real analytics service later is a new class
rather than an edit — the same shape as ``src/ports.py``.

    analytics.track("book_created", visitor, variants, destination="Prague")
    report = analytics.report()      # funnel, per-variant conversion, feedback
"""

from __future__ import annotations

import json
import logging
import statistics
import threading
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Protocol

from src.experiments import ACTIVE, Experiment

logger = logging.getLogger(__name__)

#: The funnel, in order. Each step counts *distinct visitors* who reached it.
FUNNEL = (
    ("form_view", "Opened the form"),
    ("form_submitted", "Pressed the button"),
    ("book_created", "Got a book"),
    ("artifact_opened", "Opened what they got"),
)

#: What a visitor can say on the feedback form, best to worst.
RATINGS = ("great", "fine", "poor")


@dataclass(frozen=True)
class Event:
    """One thing that happened. No PII: a visitor id, a name, and properties."""

    name: str
    visitor: str
    at: str = ""
    variants: dict[str, str] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            name=str(data.get("name", "")),
            visitor=str(data.get("visitor", "")),
            at=str(data.get("at", "")),
            variants=dict(data.get("variants") or {}),
            properties=dict(data.get("properties") or {}),
        )


class AnalyticsSink(Protocol):
    """Where events go. Implement this to send them somewhere real instead."""

    def record(self, event: Event) -> None:
        """Store one event. Must never raise into the request path."""

    def replay(self) -> Iterable[Event]:
        """Every event stored so far, for reporting."""


class NullSink:
    """Records nothing. The default when analytics are switched off."""

    def record(self, event: Event) -> None:
        return None

    def replay(self) -> Iterable[Event]:
        return ()


class JsonlSink:
    """Appends one JSON object per line, and reads them back for reports."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def record(self, event: Event) -> None:
        line = json.dumps(event.to_dict(), ensure_ascii=False)
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def replay(self) -> Iterator[Event]:
        if not self.path.is_file():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield Event.from_dict(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("skipping malformed analytics line %d", number)


class Analytics:
    """Records events and turns them back into a report."""

    def __init__(
        self,
        sink: AnalyticsSink | None = None,
        *,
        experiments: tuple[Experiment, ...] = ACTIVE,
        clock=None,
    ) -> None:
        self.sink = sink or NullSink()
        self.experiments = experiments
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    @property
    def enabled(self) -> bool:
        return not isinstance(self.sink, NullSink)

    def track(
        self,
        name: str,
        visitor: str,
        variants: dict[str, str] | None = None,
        **properties: Any,
    ) -> Event:
        """Record an event. Never raises — analytics must not break the page."""
        event = Event(
            name=name,
            visitor=visitor,
            at=self.clock(),
            variants=dict(variants or {}),
            properties={key: value for key, value in properties.items() if value is not None},
        )
        try:
            self.sink.record(event)
        except Exception:  # a broken disk must not take the form down
            logger.exception("could not record analytics event %r", name)
        return event

    def report(self) -> "Report":
        return Report.build(list(self.sink.replay()), self.experiments)


# -- reporting ------------------------------------------------------------


@dataclass(frozen=True)
class Step:
    """One rung of the funnel."""

    name: str
    label: str
    visitors: int
    #: Share of the people who reached the step above this one.
    from_previous: float
    #: Share of everyone who ever opened the form.
    from_top: float


@dataclass(frozen=True)
class VariantResult:
    """How one variant of one experiment did."""

    variant: str
    visitors: int
    conversions: int

    @property
    def rate(self) -> float:
        return self.conversions / self.visitors if self.visitors else 0.0


@dataclass(frozen=True)
class ExperimentResult:
    """One experiment's variants, with the control first."""

    key: str
    question: str
    control: str
    variants: tuple[VariantResult, ...]

    @property
    def leader(self) -> VariantResult | None:
        """The best-converting variant, or ``None`` if nobody has converted yet.

        A 0%-vs-0% tie is not a leader — there is nothing to celebrate yet.
        """
        ranked = [variant for variant in self.variants if variant.conversions]
        return max(ranked, key=lambda variant: variant.rate) if ranked else None

    def lift(self, variant: VariantResult) -> float | None:
        """How much better than the control, as a share of the control's rate."""
        baseline = next((v for v in self.variants if v.variant == self.control), None)
        if not baseline or not baseline.rate or variant.variant == self.control:
            return None
        return (variant.rate - baseline.rate) / baseline.rate

    @property
    def is_decisive(self) -> bool:
        """A crude guard against reading noise as a result.

        Not a significance test — just enough of a floor that a 1-visitor
        "100% conversion" doesn't get announced as a winner.
        """
        return all(variant.visitors >= 30 for variant in self.variants)


@dataclass(frozen=True)
class Report:
    """Everything the stats page shows."""

    events: int
    visitors: int
    funnel: tuple[Step, ...]
    experiments: tuple[ExperimentResult, ...]
    feedback: dict[str, int]
    comments: tuple[dict[str, str], ...]
    destinations: tuple[tuple[str, int], ...]
    languages: tuple[tuple[str, int], ...]
    failures: tuple[tuple[str, int], ...]
    #: (destination, language) -> how many books had a possible English leak
    #: (see src/qa.py). Not shown to whoever generated the book — see
    #: _render_result in web.py — this is the backlog instead: a destination
    #: showing up here repeatedly is missing a translated data pack or has an
    #: activity not routing its text through the locale, either way something
    #: to go fix, not something to alarm a parent about mid-print.
    qa_leaks: tuple[tuple[str, int], ...]
    median_seconds: float | None
    first_seen: str = ""
    last_seen: str = ""

    @property
    def conversion(self) -> float:
        """Books made, as a share of people who opened the form."""
        top = self.funnel[0].visitors if self.funnel else 0
        made = next((step.visitors for step in self.funnel if step.name == "book_created"), 0)
        return made / top if top else 0.0

    @property
    def feedback_score(self) -> float | None:
        """Share of feedback that was positive."""
        total = sum(self.feedback.values())
        return self.feedback.get("great", 0) / total if total else None

    @classmethod
    def build(
        cls, events: list[Event], experiments: tuple[Experiment, ...] = ACTIVE
    ) -> "Report":
        reached: dict[str, set[str]] = defaultdict(set)
        for event in events:
            reached[event.name].add(event.visitor)

        steps: list[Step] = []
        top = len(reached.get(FUNNEL[0][0], ()))
        previous = top
        for name, label in FUNNEL:
            visitors = len(reached.get(name, ()))
            steps.append(
                Step(
                    name=name,
                    label=label,
                    visitors=visitors,
                    from_previous=visitors / previous if previous else 0.0,
                    from_top=visitors / top if top else 0.0,
                )
            )
            previous = visitors

        # A visitor's variant is whatever they were assigned when they arrived.
        assigned: dict[str, dict[str, str]] = {}
        for event in events:
            if event.variants:
                assigned.setdefault(event.visitor, event.variants)

        converted = reached.get("book_created", set())
        seen = reached.get("form_view", set())
        results = []
        for experiment in experiments:
            variants = []
            for variant in experiment.variants:
                members = {
                    visitor
                    for visitor in seen
                    if assigned.get(visitor, {}).get(experiment.key) == variant
                }
                variants.append(
                    VariantResult(
                        variant=variant,
                        visitors=len(members),
                        conversions=len(members & converted),
                    )
                )
            results.append(
                ExperimentResult(
                    key=experiment.key,
                    question=experiment.question,
                    control=experiment.control,
                    variants=tuple(variants),
                )
            )

        feedback = Counter()
        comments = []
        destinations = Counter()
        languages = Counter()
        failures = Counter()
        qa_leaks = Counter()
        durations = []
        for event in events:
            properties = event.properties
            if event.name == "feedback":
                rating = str(properties.get("rating", ""))
                if rating:
                    feedback[rating] += 1
                comment = str(properties.get("comment", "")).strip()
                if comment:
                    comments.append(
                        {"rating": rating, "comment": comment, "at": event.at}
                    )
            elif event.name == "book_created":
                if properties.get("destination"):
                    destinations[str(properties["destination"])] += 1
                if properties.get("language"):
                    languages[str(properties["language"])] += 1
                if isinstance(properties.get("seconds"), (int, float)):
                    durations.append(float(properties["seconds"]))
                if properties.get("language_qa_leaks"):
                    qa_leaks[
                        f"{properties.get('destination', '?')} ({properties.get('language', '?')})"
                    ] += 1
            elif event.name == "generate_failed":
                failures[str(properties.get("reason", "unknown"))] += 1

        stamps = sorted(event.at for event in events if event.at)
        return cls(
            events=len(events),
            visitors=len({event.visitor for event in events if event.visitor}),
            funnel=tuple(steps),
            experiments=tuple(results),
            feedback={rating: feedback.get(rating, 0) for rating in RATINGS},
            comments=tuple(reversed(comments[-12:])),
            destinations=tuple(destinations.most_common(8)),
            languages=tuple(languages.most_common()),
            failures=tuple(failures.most_common(5)),
            qa_leaks=tuple(qa_leaks.most_common(8)),
            median_seconds=statistics.median(durations) if durations else None,
            first_seen=stamps[0] if stamps else "",
            last_seen=stamps[-1] if stamps else "",
        )


def build_analytics(output_root: Path | str, *, enabled: bool = True) -> Analytics:
    """The default wiring: a JSONL file tucked beside the generated books."""
    if not enabled:
        return Analytics(NullSink())
    return Analytics(JsonlSink(Path(output_root) / ".analytics" / "events.jsonl"))
