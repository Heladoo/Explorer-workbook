"""Event recording and the funnel/experiment/feedback report built from it."""

from __future__ import annotations

import json

import pytest

from src.analytics import (
    Analytics,
    Event,
    JsonlSink,
    NullSink,
    Report,
    build_analytics,
)
from src.experiments import Experiment

EXPERIMENTS = (
    Experiment(key="cta", variants=("control", "variant"), question="Does wording matter?"),
)


class MemorySink:
    """An in-memory sink for tests — no disk, easy to inspect."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def record(self, event: Event) -> None:
        self.events.append(event)

    def replay(self):
        return list(self.events)


def _tick():
    """A clock that advances one second per call, for deterministic ordering."""
    state = {"n": 0}

    def clock():
        state["n"] += 1
        return f"2026-01-01T00:00:{state['n']:02d}+00:00"

    return clock


@pytest.fixture
def analytics() -> Analytics:
    return Analytics(MemorySink(), experiments=EXPERIMENTS, clock=_tick())


# -- Event ------------------------------------------------------------


def test_event_round_trips_through_a_dict():
    event = Event(
        name="book_created",
        visitor="v1",
        at="2026-01-01T00:00:00+00:00",
        variants={"cta": "control"},
        properties={"destination": "Prague"},
    )
    restored = Event.from_dict(json.loads(json.dumps(event.to_dict())))
    assert restored == event


def test_event_from_dict_tolerates_missing_fields():
    event = Event.from_dict({"name": "form_view"})
    assert event.visitor == ""
    assert event.variants == {}
    assert event.properties == {}


# -- sinks --------------------------------------------------------------


def test_null_sink_records_nothing():
    sink = NullSink()
    sink.record(Event(name="x", visitor="v1"))
    assert list(sink.replay()) == []


def test_jsonl_sink_persists_and_replays(tmp_path):
    sink = JsonlSink(tmp_path / "events.jsonl")
    sink.record(Event(name="form_view", visitor="v1", at="t1"))
    sink.record(Event(name="book_created", visitor="v1", at="t2"))

    replayed = list(sink.replay())
    assert [event.name for event in replayed] == ["form_view", "book_created"]


def test_jsonl_sink_creates_its_parent_directory(tmp_path):
    sink = JsonlSink(tmp_path / "nested" / "dir" / "events.jsonl")
    sink.record(Event(name="form_view", visitor="v1"))
    assert (tmp_path / "nested" / "dir" / "events.jsonl").exists()


def test_jsonl_sink_replay_of_a_missing_file_is_empty(tmp_path):
    sink = JsonlSink(tmp_path / "never-written.jsonl")
    assert list(sink.replay()) == []


def test_jsonl_sink_skips_a_corrupt_line(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        json.dumps({"name": "form_view", "visitor": "v1"}) + "\n"
        "not json at all\n"
        + json.dumps({"name": "book_created", "visitor": "v1"}) + "\n",
        encoding="utf-8",
    )
    sink = JsonlSink(path)
    names = [event.name for event in sink.replay()]
    assert names == ["form_view", "book_created"]


def test_jsonl_sink_keeps_unicode_readable(tmp_path):
    sink = JsonlSink(tmp_path / "events.jsonl")
    sink.record(Event(name="book_created", visitor="v1", properties={"destination": "כפר הנוקדים"}))
    raw = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert "כפר הנוקדים" in raw, "ensure_ascii=False keeps it human-readable on disk"


# -- Analytics.track ------------------------------------------------------


def test_track_calls_the_sink(analytics):
    analytics.track("form_view", "v1", {"cta": "control"}, destination="Prague")

    events = analytics.sink.events
    assert len(events) == 1
    assert events[0].name == "form_view"
    assert events[0].visitor == "v1"
    assert events[0].variants == {"cta": "control"}
    assert events[0].properties == {"destination": "Prague"}
    assert events[0].at == "2026-01-01T00:00:01+00:00"


def test_track_drops_none_valued_properties(analytics):
    analytics.track("form_view", "v1", reason=None, destination="Prague")
    assert analytics.sink.events[0].properties == {"destination": "Prague"}


def test_a_broken_sink_does_not_raise():
    class Exploding:
        def record(self, event):
            raise OSError("disk is full")

        def replay(self):
            return []

    analytics = Analytics(Exploding())
    analytics.track("form_view", "v1")  # must not raise


def test_enabled_reflects_the_sink():
    assert not Analytics(NullSink()).enabled
    assert Analytics(JsonlSink("/tmp/doesnotmatter.jsonl")).enabled


def test_build_analytics_disabled_uses_the_null_sink(tmp_path):
    result = build_analytics(tmp_path, enabled=False)
    assert not result.enabled


def test_build_analytics_enabled_writes_under_the_output_root(tmp_path):
    result = build_analytics(tmp_path, enabled=True)
    result.track("form_view", "v1")
    assert (tmp_path / ".analytics" / "events.jsonl").exists()


# -- Report: funnel -------------------------------------------------------


def test_funnel_counts_distinct_visitors_per_step(analytics):
    for visitor in ("a", "b", "c"):
        analytics.track("form_view", visitor)
    for visitor in ("a", "b"):
        analytics.track("form_submitted", visitor)
    analytics.track("book_created", "a")

    report = analytics.report()
    by_name = {step.name: step for step in report.funnel}
    assert by_name["form_view"].visitors == 3
    assert by_name["form_submitted"].visitors == 2
    assert by_name["book_created"].visitors == 1
    assert by_name["book_created"].from_top == pytest.approx(1 / 3)
    assert by_name["form_submitted"].from_previous == pytest.approx(2 / 3)


def test_a_repeated_event_from_one_visitor_counts_once(analytics):
    analytics.track("form_view", "a")
    analytics.track("form_view", "a")
    analytics.track("form_view", "a")

    assert analytics.report().funnel[0].visitors == 1


def test_empty_report_does_not_divide_by_zero():
    report = Report.build([])
    assert report.funnel[0].visitors == 0
    assert report.conversion == 0.0
    assert report.feedback_score is None
    assert report.median_seconds is None


def test_conversion_is_book_created_over_form_view(analytics):
    for visitor in "abcd":
        analytics.track("form_view", visitor)
    for visitor in "ab":
        analytics.track("book_created", visitor)

    assert analytics.report().conversion == pytest.approx(0.5)


# -- Report: experiments ---------------------------------------------------


def test_experiment_conversion_is_computed_per_variant(analytics):
    # 2 in "control", 1 converts; 2 in "variant", both convert.
    analytics.track("form_view", "c1", {"cta": "control"})
    analytics.track("form_view", "c2", {"cta": "control"})
    analytics.track("form_view", "v1", {"cta": "variant"})
    analytics.track("form_view", "v2", {"cta": "variant"})
    analytics.track("book_created", "c1")
    analytics.track("book_created", "v1")
    analytics.track("book_created", "v2")

    report = analytics.report()
    result = next(r for r in report.experiments if r.key == "cta")
    control = next(v for v in result.variants if v.variant == "control")
    variant = next(v for v in result.variants if v.variant == "variant")

    assert control.visitors == 2 and control.conversions == 1
    assert variant.visitors == 2 and variant.conversions == 2
    assert control.rate == pytest.approx(0.5)
    assert variant.rate == pytest.approx(1.0)


def test_lift_is_relative_to_the_control(analytics):
    for i in range(10):
        analytics.track("form_view", f"c{i}", {"cta": "control"})
    for i in range(2):
        analytics.track("book_created", f"c{i}")  # 20% control
    for i in range(10):
        analytics.track("form_view", f"v{i}", {"cta": "variant"})
    for i in range(3):
        analytics.track("book_created", f"v{i}")  # 30% variant

    result = next(r for r in analytics.report().experiments if r.key == "cta")
    variant = next(v for v in result.variants if v.variant == "variant")
    assert result.lift(variant) == pytest.approx(0.5)  # 50% relative lift


def test_lift_of_the_control_against_itself_is_none(analytics):
    analytics.track("form_view", "c1", {"cta": "control"})
    result = analytics.report().experiments[0]
    control = result.variants[0]
    assert result.lift(control) is None


def test_leader_picks_the_highest_converting_variant_with_traffic(analytics):
    analytics.track("form_view", "c1", {"cta": "control"})
    analytics.track("form_view", "v1", {"cta": "variant"})
    analytics.track("form_view", "v2", {"cta": "variant"})
    analytics.track("book_created", "v1")
    analytics.track("book_created", "v2")

    result = analytics.report().experiments[0]
    assert result.leader.variant == "variant"


def test_leader_is_none_when_nobody_converted(analytics):
    analytics.track("form_view", "c1", {"cta": "control"})
    analytics.track("form_view", "v1", {"cta": "variant"})
    result = analytics.report().experiments[0]
    assert result.leader is None


def test_is_decisive_requires_enough_traffic_per_variant(analytics):
    analytics.track("form_view", "c1", {"cta": "control"})
    analytics.track("form_view", "v1", {"cta": "variant"})

    report = analytics.report()
    assert not report.experiments[0].is_decisive


def test_is_decisive_once_both_variants_clear_the_floor(analytics):
    for i in range(30):
        analytics.track("form_view", f"c{i}", {"cta": "control"})
        analytics.track("form_view", f"v{i}", {"cta": "variant"})

    assert analytics.report().experiments[0].is_decisive


def test_a_visitors_variant_is_fixed_by_their_first_recorded_assignment(analytics):
    """Even if later events carry different variants, the first one sticks."""
    analytics.track("form_view", "v1", {"cta": "control"})
    analytics.track("form_submitted", "v1", {"cta": "variant"})  # should be ignored
    analytics.track("book_created", "v1")

    result = analytics.report().experiments[0]
    control = next(v for v in result.variants if v.variant == "control")
    assert control.visitors == 1 and control.conversions == 1


# -- Report: feedback, destinations, failures -----------------------------


def test_feedback_ratings_are_tallied(analytics):
    analytics.track("feedback", "v1", rating="great", comment="")
    analytics.track("feedback", "v2", rating="great", comment="")
    analytics.track("feedback", "v3", rating="poor", comment="too slow")

    report = analytics.report()
    assert report.feedback == {"great": 2, "fine": 0, "poor": 1}
    assert report.feedback_score == pytest.approx(2 / 3)


def test_only_comments_with_text_are_kept_for_display(analytics):
    analytics.track("feedback", "v1", rating="great", comment="")
    analytics.track("feedback", "v2", rating="poor", comment="  ")
    analytics.track("feedback", "v3", rating="great", comment="nice!")

    report = analytics.report()
    assert len(report.comments) == 1
    assert report.comments[0]["comment"] == "nice!"


def test_comments_are_newest_first(analytics):
    analytics.track("feedback", "v1", rating="great", comment="first")
    analytics.track("feedback", "v2", rating="great", comment="second")

    report = analytics.report()
    assert [c["comment"] for c in report.comments] == ["second", "first"]


def test_comments_are_capped(analytics):
    for i in range(20):
        analytics.track("feedback", f"v{i}", rating="great", comment=f"comment {i}")
    assert len(analytics.report().comments) == 12


def test_destinations_and_languages_are_counted(analytics):
    analytics.track("book_created", "v1", destination="Prague", language="en")
    analytics.track("book_created", "v2", destination="Prague", language="en")
    analytics.track("book_created", "v3", destination="Kfar Hanokdim", language="he")

    report = analytics.report()
    assert dict(report.destinations)["Prague"] == 2
    assert dict(report.languages)["he"] == 1


def test_median_build_time_ignores_events_without_a_duration(analytics):
    analytics.track("book_created", "v1", seconds=1.0)
    analytics.track("book_created", "v2", seconds=3.0)
    analytics.track("book_created", "v3")  # no timing recorded

    assert analytics.report().median_seconds == pytest.approx(2.0)


def test_failures_are_grouped_by_reason(analytics):
    analytics.track("generate_failed", "v1", reason="destination is required")
    analytics.track("generate_failed", "v2", reason="destination is required")
    analytics.track("generate_failed", "v3", reason="ValueError")

    failures = dict(analytics.report().failures)
    assert failures["destination is required"] == 2
    assert failures["ValueError"] == 1
