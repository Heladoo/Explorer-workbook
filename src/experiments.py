"""A/B experiments.

Assignment is a hash of the experiment key and the visitor id, so it is stable
for a visitor without storing anything, identical across processes, and evenly
split. Adding an experiment is one entry in :data:`ACTIVE`; the form template
reads the chosen variant and the stats page reports conversion per variant.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Experiment:
    """One thing being tested, and the variants it is split between."""

    key: str
    variants: tuple[str, ...]
    question: str = ""

    def __post_init__(self) -> None:
        if len(self.variants) < 2:
            raise ValueError(f"experiment {self.key!r} needs at least two variants")
        if len(set(self.variants)) != len(self.variants):
            raise ValueError(f"experiment {self.key!r} has duplicate variants")

    @property
    def control(self) -> str:
        """The first variant, treated as the baseline when reporting."""
        return self.variants[0]

    def assign(self, visitor: str) -> str:
        """Pick this visitor's variant — same answer every time, no storage."""
        digest = hashlib.sha256(f"{self.key}:{visitor}".encode("utf-8")).digest()
        return self.variants[int.from_bytes(digest[:4], "big") % len(self.variants)]


#: The experiments currently running. Keep this short — every extra experiment
#: splits the same traffic further and slows down every result.
ACTIVE: tuple[Experiment, ...] = (
    Experiment(
        key="cta",
        variants=("make_my_book", "build_it"),
        question="Does a more concrete call to action get more books made?",
    ),
    Experiment(
        key="optional_fields",
        variants=("visible", "tucked"),
        question="Do the optional fields help, or do they scare people off?",
    ),
)


def assignments(visitor: str, experiments: tuple[Experiment, ...] = ACTIVE) -> dict[str, str]:
    """Every active experiment's variant for one visitor."""
    return {experiment.key: experiment.assign(visitor) for experiment in experiments}


def find(key: str, experiments: tuple[Experiment, ...] = ACTIVE) -> Experiment | None:
    for experiment in experiments:
        if experiment.key == key:
            return experiment
    return None
