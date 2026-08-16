"""Scavenger Hunt: a table of things to spot on the real trip.

Two things make this page work, and both are deliberate departures from how the
rest of the book is illustrated:

**The table is typeset, not drawn.** The grid, the checkboxes and the words are
page furniture the print layout builds. Asking one image prompt for "a grid of
twelve labelled cells, each with an empty checkbox" is asking an image model
for exactly what it is worst at — exact counts, one specific thing per cell,
and no stray text.

**Each picture is its own prompt.** One symbol per prompt ("a single stop
sign, centred") is what image models are reliable at, and it means a wrong
picture costs one retry instead of the whole page.

**The items are mostly ordinary.** A hunt built only from a destination's
landmarks and wildlife is unfinishable — those things appear once, if at all.
Most cells are everyday sights (a stop sign, a bridge, a police car) that a
child can find on the way to anywhere; a few come from the destination so the
page still belongs to this trip. See :mod:`src.activities._symbols`.
"""

from __future__ import annotations

from src.activities._symbols import (
    UNIVERSAL_SYMBOLS,
    Symbol,
    destination_symbols,
    grid_dimensions,
    hunt_size,
)
from src.activities.base import (
    ActivityGenerator,
    PlannedPage,
    register_activity,
)
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft, SymbolBrief


def _has_spot_role(symbol: Symbol) -> bool:
    """Whether ``symbol`` is eligible for the hunt at all.

    A destination-minted symbol (``facets is None`` — nothing in the library
    matched it) carries no role restriction and is always eligible. A
    library entry has to declare ``spot`` explicitly — some are ``shadow``-
    or ``pack``-only (too rare to actually find, or something you'd bring
    rather than spot), and would otherwise still surface here since nothing
    else in the selection below checks ``roles`` for anything but ``pack``.
    """
    return symbol.facets is None or "spot" in symbol.facets.roles


def _spot_eligible(symbol: Symbol) -> bool:
    """Whether ``symbol`` may appear on the hunt sheet at all.

    Requires :func:`_has_spot_role` *and* excludes anything ``pack``-only —
    something to bring, not something to spot, and the packing page already
    owns those. Applied to both pools the sheet draws from: before this,
    only the universal side (``findable`` below) excluded pack-only symbols,
    so a destination match like sunscreen or hiking shoes could still slip
    in from ``local_pool``.
    """
    if not _has_spot_role(symbol):
        return False
    return "pack" not in (symbol.facets.roles if symbol.facets else ())


@register_activity
class ScavengerHuntActivity(ActivityGenerator):
    """A picture checklist of real things to find, mostly everyday ones."""

    activity_type = "scavenger_hunt"
    display_name = "Scavenger Hunt"
    educational_goal = (
        "Turns travelling itself into an active search: builds observation skills "
        "and vocabulary by sending the child looking for the real thing, not a "
        "drawing of it."
    )
    min_age = 4
    max_age = 12
    weight = 14
    energy = "active"
    # Raised so the book has enough active-energy supply to alternate against
    # calm pages now that hidden_objects/spot_difference are paused (see their
    # `enabled = False`) — with only 3 active activity types left, capping
    # each at 1 left books tailing off into a long run of calm pages.
    max_per_workbook = 3

    def supports(self, context: WorkbookContext) -> bool:
        # The universal pool works anywhere, so unlike most activities this one
        # needs no destination knowledge at all to make a good page.
        return super().supports(context)

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        symbols = self._choose(context, planned)
        labels = [self._label(context, symbol) for symbol in symbols]
        columns, rows = grid_dimensions(len(symbols))

        return self.draft(
            title=self.text(
                context, "scavenger_hunt.title", destination=context.display_destination
            ),
            instructions=self.text(
                context, "scavenger_hunt.instructions", count=len(symbols)
            ),
            planned=planned,
            symbols=tuple(
                SymbolBrief(
                    key=symbol.key,
                    label=self._label(context, symbol),
                    subject=symbol.subject,
                    universal=symbol.universal,
                )
                for symbol in symbols
            ),
            metadata={
                "items": labels,
                "item_count": len(symbols),
                "symbol_keys": [symbol.key for symbol in symbols],
                "columns": columns,
                "rows": rows,
                #: The grid is typeset entirely from ``symbols`` above — the
                #: page carries no illustration of its own.
                "needs_illustration": False,
            },
        )

    # -- internals -------------------------------------------------------

    def _label(self, context: WorkbookContext, symbol: Symbol) -> str:
        """What the child reads under the picture, in the workbook's language.

        Destination sights are already in the workbook's language — they came
        out of a translated knowledge pack — so only the universal bank, which
        is defined in English, needs the locale lookup.
        """
        if not symbol.universal:
            return symbol.label
        return self.strings(context).optional(f"symbol.{symbol.key}", symbol.label)

    def _choose(self, context: WorkbookContext, planned: PlannedPage) -> tuple[Symbol, ...]:
        """Pick the sheet: mostly universal symbols, seasoned with real sights."""
        total, wanted_local = hunt_size(planned.difficulty)
        key = f"scavenger_hunt:{planned.number}"

        local_pool = tuple(s for s in destination_symbols(context) if _spot_eligible(s))
        local = _sample(context, local_pool, wanted_local, f"{key}:local")

        # A destination phrase can resolve onto a library symbol that is
        # *also* in the always-findable universal pool (a common/everywhere
        # entry, matched by key or alias — see destination_symbols()), so
        # exclude whatever `local` already picked before topping up, or the
        # same symbol could be sampled into both halves and print twice.
        local_keys = {symbol.key for symbol in local}
        findable = tuple(
            symbol
            for symbol in UNIVERSAL_SYMBOLS
            if symbol.key not in local_keys and _spot_eligible(symbol)
        )

        # Whatever the destination could not supply is topped up from the
        # universal pool, preferring the always-findable "everywhere" tier —
        # the "common" tier only fills whatever "everywhere" alone can't.
        wanted_universal = total - len(local)
        everywhere = tuple(s for s in findable if s.facets.ubiquity == "everywhere")
        universal = _sample(context, everywhere, wanted_universal, f"{key}:universal")

        remaining = wanted_universal - len(universal)
        if remaining > 0:
            picked_keys = {symbol.key for symbol in universal}
            rest = tuple(s for s in findable if s.key not in picked_keys)
            universal.extend(_sample(context, rest, remaining, f"{key}:universal:rest"))

        chosen = [*universal, *local]
        # Shuffle so the destination sights are scattered through the grid
        # rather than sitting in a block at the end.
        context.rng_for(f"{key}:order").shuffle(chosen)
        return tuple(chosen)


def _sample(
    context: WorkbookContext, pool: tuple[Symbol, ...], count: int, key: str
) -> list[Symbol]:
    """Deterministically take ``count`` symbols from ``pool``.

    ``context.sample`` works on strings, so this samples the keys and maps
    back — keeping every random choice on the seeded RNG the whole project
    relies on for reproducible output.
    """
    if count <= 0 or not pool:
        return []
    by_key = {symbol.key: symbol for symbol in pool}
    picked = context.sample(tuple(by_key), min(count, len(by_key)), key=key)
    return [by_key[symbol_key] for symbol_key in picked]
