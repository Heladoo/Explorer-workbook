"""The route map: one illustrated page over the real itinerary, in order.

Gated on itinerary length rather than knowledge — a one- or two-stop
itinerary is just an origin and a destination, not a route worth drawing.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from src.activities.base import get_generator
from src.models.context import DestinationKnowledge, Trip, WorkbookContext
from src.models.page import RenderMode
from src.models.plan import PlannedPage

_HEBREW = re.compile(r"[֐-׿]")


def _slot(number: int = 5) -> PlannedPage:
    return PlannedPage(number=number, activity_type="map", difficulty="medium")


def _context(itinerary: tuple[str, ...]) -> WorkbookContext:
    return WorkbookContext(
        destination="Somewhere",
        knowledge=DestinationKnowledge(source="test"),
        trip=Trip(itinerary=itinerary),
    )


# -- supports() is gated on itinerary length --------------------------------


@pytest.mark.parametrize("length", [0, 1, 2])
def test_unsupported_below_three_stops(length):
    itinerary = tuple(f"Stop {i}" for i in range(length))
    assert not get_generator("map").supports(_context(itinerary))


@pytest.mark.parametrize("length", [3, 4, 6])
def test_supported_from_three_stops(length):
    itinerary = tuple(f"Stop {i}" for i in range(length))
    assert get_generator("map").supports(_context(itinerary))


# -- the generated draft -----------------------------------------------------


def test_the_route_follows_the_itinerary_in_order():
    itinerary = ("Athens", "Volos", "Pelion village", "Milina")
    draft = get_generator("map").generate(_context(itinerary), _slot())

    brief = draft.image_brief
    assert brief is not None
    assert brief.elements == itinerary
    assert itinerary[0] in brief.scene
    assert itinerary[-1] in brief.scene
    assert brief.render_mode in RenderMode.ALL
    assert draft.metadata["itinerary"] == list(itinerary)
    assert draft.metadata["stop_count"] == len(itinerary)


def test_needs_no_symbol_grid():
    """A route map is one picture, not a table of small pictures."""
    itinerary = ("A", "B", "C")
    draft = get_generator("map").generate(_context(itinerary), _slot())
    assert draft.symbols == ()


def test_generation_is_deterministic():
    itinerary = ("A", "B", "C", "D")
    context = _context(itinerary)
    slot = _slot()
    assert get_generator("map").generate(context, slot) == get_generator("map").generate(
        context, slot
    )


def test_a_short_itinerary_still_produces_a_sane_draft():
    """generate() itself must not crash when called outside supports()'s own
    gate — a bare destination with no itinerary at all falls back to just
    the destination name."""
    draft = get_generator("map").generate(_context(()), _slot())
    assert draft.title.strip()
    assert draft.instructions.strip()
    assert draft.image_brief is not None
    assert draft.image_brief.subject.strip()
    assert all(element.strip() for element in draft.image_brief.elements)


def test_the_title_names_the_destination():
    itinerary = ("A", "B", "C")
    draft = get_generator("map").generate(
        replace(_context(itinerary), destination="Pelion"), _slot()
    )
    assert "Pelion" in draft.title


def test_a_hebrew_map_is_translated():
    itinerary = ("Athens", "Volos", "Pelion village")
    context = replace(_context(itinerary), language="he")
    draft = get_generator("map").generate(context, _slot())
    assert _HEBREW.search(draft.title)
    assert _HEBREW.search(draft.instructions)
    # The image prompt itself must stay English — only what the child reads
    # is translated (see the itinerary stops, which are proper nouns and
    # untouched either way).
    assert draft.image_brief.elements == itinerary
