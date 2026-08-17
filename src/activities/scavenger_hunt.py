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


#: How many "animals" one sheet may show. The universal pool's animal topic
#: is the deepest of any (16 of 45 entries), and destination wildlife sights
#: lean the same way — left unchecked, an unlucky draw reads as a zoo
#: checklist rather than the "mostly everyday things" hunt the module
#: docstring describes.
_MAX_ANIMALS = 3


def _is_animal(symbol: Symbol) -> bool:
    """Whether ``symbol`` counts against ``_MAX_ANIMALS``.

    A symbol minted fresh from a destination phrase with no library match at
    all (``facets is None``) is never counted here — every wildlife-sourced
    local symbol across every curated destination pack resolves to a real
    library entry today (spot-checked across Pelion, Kfar Hanokdim and
    Prague), so this only misses a genuinely new wildlife phrase with
    committed art but no library registration, which would simply not be
    capped — a narrower gap than guessing "animal" from a bare English
    phrase with no facets to check at all.
    """
    return symbol.facets is not None and symbol.facets.topic == "animals"


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
    # Capped at 1, unlike maze/matching (still 3): a repeat hunt reuses the
    # same "mostly everyday things" item pool, so a second or third one in
    # the same book reads as a near-duplicate rather than a fresh puzzle —
    # maze and matching stay varied on a repeat (a new layout, a new set of
    # shadows), a hunt mostly doesn't. maze+matching alone (3+3=6) still
    # supply enough active-energy pages to alternate against calm ones —
    # see their own `max_per_workbook` comment for why that headroom exists
    # at all (hidden_objects/spot_difference are paused, `enabled = False`).
    max_per_workbook = 1

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
        chosen = self._cap_animals(context, key, chosen, local_keys, local_pool, findable)
        # Shuffle so the destination sights are scattered through the grid
        # rather than sitting in a block at the end.
        context.rng_for(f"{key}:order").shuffle(chosen)
        return tuple(chosen)

    def _cap_animals(
        self,
        context: WorkbookContext,
        key: str,
        chosen: list[Symbol],
        local_keys: set[str],
        *fallback_pools: tuple[Symbol, ...],
    ) -> list[Symbol]:
        """Swap any animal past the third for a non-animal alternative.

        Runs as a correction after the sheet is otherwise full, rather than
        constraining the selection above from scratch — every guarantee that
        selection already provides for a non-animal symbol (eligibility, no
        duplicates) is exactly as true for its replacement, since
        replacements are drawn from the very same pools.

        Trims universal-pool animals first, local ones only if that alone
        isn't enough: a local wildlife sight is the scarce, trip-specific
        ingredient the class docstring calls out ("a few come from the
        destination so the page still belongs to this trip"), while the
        universal pool's animal topic is deep (16 of 45 entries) and always
        has a same-tier non-animal alternative to swap in instead. Capping
        the *count* without this bias risks trimming exactly the sights that
        make the sheet belong to this destination in the first place — a
        real case: a two-sight, both-animals wildlife pool losing both to a
        larger crop of universal animals it happened to be sampled next to.

        Falls back to keeping an extra animal rather than shrinking the
        sheet if the non-animal pools ever come up short — "the sheet is
        always full" is the harder guarantee (see
        ``test_the_sheet_is_always_full``); in practice the universal pool
        alone has ~29 non-animal entries, far more than any sheet needs, so
        this should never bite.
        """
        animal_count = sum(1 for symbol in chosen if _is_animal(symbol))
        if animal_count <= _MAX_ANIMALS:
            return chosen

        universal_animals = [
            symbol for symbol in chosen if _is_animal(symbol) and symbol.key not in local_keys
        ]
        local_animals = [
            symbol for symbol in chosen if _is_animal(symbol) and symbol.key in local_keys
        ]

        to_drop = animal_count - _MAX_ANIMALS
        drop_universal = min(to_drop, len(universal_animals))
        drop_keys = set(
            context.sample(
                tuple(symbol.key for symbol in universal_animals),
                drop_universal,
                key=f"{key}:animal_cap:universal",
            )
        )

        still_to_drop = to_drop - drop_universal
        if still_to_drop > 0:
            drop_keys |= set(
                context.sample(
                    tuple(symbol.key for symbol in local_animals),
                    still_to_drop,
                    key=f"{key}:animal_cap:local",
                )
            )

        kept = [symbol for symbol in chosen if symbol.key not in drop_keys]

        used_keys = {symbol.key for symbol in kept}
        by_key: dict[str, Symbol] = {}
        for pool in fallback_pools:
            for symbol in pool:
                if not _is_animal(symbol) and symbol.key not in used_keys:
                    by_key.setdefault(symbol.key, symbol)
        replacements = _sample(
            context, tuple(by_key.values()), len(drop_keys), f"{key}:animal_cap:replace"
        )

        if len(replacements) < len(drop_keys):
            dropped = [symbol for symbol in chosen if symbol.key in drop_keys]
            have = {symbol.key for symbol in replacements}
            replacements += [s for s in dropped if s.key not in have][
                : len(drop_keys) - len(replacements)
            ]

        return kept + replacements


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
