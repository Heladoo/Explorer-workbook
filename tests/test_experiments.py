"""A/B assignment: stable, storage-free, and evenly split."""

from __future__ import annotations

import pytest

from src.experiments import ACTIVE, Experiment, assignments, find


def test_assignment_is_stable_for_the_same_visitor():
    experiment = Experiment(key="cta", variants=("a", "b"))
    first = experiment.assign("visitor-1")
    second = experiment.assign("visitor-1")
    assert first == second


def test_different_visitors_can_land_in_different_variants():
    experiment = Experiment(key="cta", variants=("a", "b"))
    variants = {experiment.assign(f"visitor-{i}") for i in range(200)}
    assert variants == {"a", "b"}, "200 visitors should exercise both arms"


def test_assignment_only_returns_declared_variants():
    experiment = Experiment(key="cta", variants=("a", "b", "c"))
    for i in range(100):
        assert experiment.assign(f"v{i}") in ("a", "b", "c")


def test_split_is_roughly_even():
    experiment = Experiment(key="cta", variants=("a", "b"))
    counts = {"a": 0, "b": 0}
    for i in range(2000):
        counts[experiment.assign(f"visitor-{i}")] += 1
    ratio = counts["a"] / 2000
    assert 0.4 < ratio < 0.6, f"split was {ratio:.2f}, expected close to 0.5"


def test_a_different_experiment_key_gives_an_independent_split():
    """The same visitor can land differently in two unrelated experiments."""
    cta = Experiment(key="cta", variants=("a", "b"))
    other = Experiment(key="something_else", variants=("a", "b"))
    visitors = [f"visitor-{i}" for i in range(50)]
    cta_variants = [cta.assign(v) for v in visitors]
    other_variants = [other.assign(v) for v in visitors]
    assert cta_variants != other_variants, "different keys must not always agree"


def test_control_is_the_first_variant():
    experiment = Experiment(key="cta", variants=("baseline", "new"))
    assert experiment.control == "baseline"


def test_needs_at_least_two_variants():
    with pytest.raises(ValueError, match="at least two variants"):
        Experiment(key="cta", variants=("only_one",))


def test_rejects_duplicate_variants():
    with pytest.raises(ValueError, match="duplicate"):
        Experiment(key="cta", variants=("a", "a"))


def test_assignments_covers_every_active_experiment():
    result = assignments("someone")
    assert set(result) == {experiment.key for experiment in ACTIVE}
    for experiment in ACTIVE:
        assert result[experiment.key] in experiment.variants


def test_assignments_can_take_a_custom_experiment_set():
    custom = (Experiment(key="only_this", variants=("x", "y")),)
    result = assignments("someone", custom)
    assert set(result) == {"only_this"}


def test_find_returns_the_named_experiment():
    experiment = find("cta")
    assert experiment is not None
    assert experiment.key == "cta"


def test_find_returns_none_for_an_unknown_key():
    assert find("does_not_exist") is None


def test_active_experiments_are_well_formed():
    """A guard against a typo turning an experiment into a crash at runtime."""
    keys = [experiment.key for experiment in ACTIVE]
    assert len(keys) == len(set(keys)), "experiment keys must be unique"
    for experiment in ACTIVE:
        assert len(experiment.variants) >= 2
        assert experiment.question, f"{experiment.key} should explain what it's testing"
