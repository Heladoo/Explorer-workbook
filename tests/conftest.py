"""Shared fixtures.

``sys.path`` is extended so the tests run from a clean checkout with no install
step — the project is stdlib-only by design.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.destination_agent import build_knowledge_agent  # noqa: E402
from src.models.context import Child, DestinationKnowledge, Trip, WorkbookContext  # noqa: E402
from src.models.plan import PlannedPage  # noqa: E402
from src.pipeline import WorkbookBuilder  # noqa: E402

DATA_DIR = ROOT / "data" / "destinations"


@pytest.fixture
def knowledge() -> DestinationKnowledge:
    """A small but complete knowledge set, independent of the shipped packs."""
    return DestinationKnowledge(
        landmarks=("the old lighthouse", "the harbour wall", "the cliff path"),
        wildlife=("puffins", "grey seals", "crabs", "gannets"),
        plants=("sea thrift", "marram grass"),
        activities=("a boat trip", "rock pooling", "climbing the lighthouse"),
        history=("sailors have used this light for 200 years",),
        local_food=("fish pie", "seaweed crackers"),
        weather=("windy and cool", "sudden rain showers"),
        interesting_facts=("Puffins dig burrows to nest in.",),
        source="test",
    )


@pytest.fixture
def context(knowledge: DestinationKnowledge) -> WorkbookContext:
    return WorkbookContext(
        destination="Lighthouse Point",
        knowledge=knowledge,
        children=(Child("Noa", 5), Child("Amit", 7)),
        trip=Trip(itinerary=("Harbour day", "Cliff walk"), duration_days=2),
        page_count=12,
    )


@pytest.fixture
def planned() -> PlannedPage:
    return PlannedPage(number=2, activity_type="coloring", difficulty="medium", target_age=6)


@pytest.fixture
def builder() -> WorkbookBuilder:
    """A builder pinned to the curated packs and a fixed clock, for determinism."""
    return WorkbookBuilder(
        knowledge_agent=build_knowledge_agent("file", data_dir=DATA_DIR),
        clock=lambda: "2026-01-01T00:00:00+00:00",
    )


#: Set WORKBOOK_TEST_PDF=1 to see the real Chromium/Playwright behaviour in the
#: web-form tests, e.g. while writing a new test against actual PDF output.
FORCE_REAL_PDF = os.environ.get("WORKBOOK_TEST_PDF") == "1"


def patch_pdf_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip ``src.web``'s real Chromium probe for a test server, unless forced.

    Playwright is installed in this environment, so ``src.web._pdf_available()``
    is always ``True`` — every ``/generate`` call renders a full PDF (~4s) even
    though almost none of the web-form tests ever look at it. Tests that
    actually exercise PDF output (the ``/print`` tests in ``test_web.py``) undo
    this patch themselves before the call that needs it real.
    """
    if not FORCE_REAL_PDF:
        monkeypatch.setattr("src.web._pdf_available", lambda: False)
