"""Pack the Bag: connect what belongs, spot what doesn't.

Used to ask one image model call for a grid of a dozen labelled objects with
empty checkboxes beside them — exactly the kind of exact-count, exact-layout,
no-stray-text prompt an image model gets wrong. It also had no way to be
*wrong* about anything: every item printed was something to tick off, so the
page taught packing but never judgement.

Both problems have the same fix the scavenger hunt and matching pages already
use: stop asking for the whole page in one prompt, and ask for one small
drawing per item instead (a :class:`SymbolBrief` each, drawn from the shared,
cached symbol library — see ``src/activities/_symbols.py`` and
``data/symbols/library.json``). The print layout (``@layout("packing")`` in
``src/rendering/layouts.py``) then arranges them in a ring around a backpack,
and the child draws their own line from each thing to the backpack — no
checkbox, no printed label, nothing for an image model to get wrong.

The judgement part comes from a second pool: a few things that do *not*
belong on this trip — a winter coat and skis for a desert crossing, a sun hat
and flip-flops for a snowy one — drawn from the same library, using the
opposite of whatever climate the destination's own weather knowledge matched.
Nothing here marks which is which on the page itself; only the metadata
(``pack_keys`` / ``distractor_keys``) knows, for the answer key.
"""

from __future__ import annotations

from src.activities._symbols import Symbol
from src.activities.base import (
    ActivityGenerator,
    PlannedPage,
    register_activity,
)
from src.models.context import WorkbookContext
from src.models.page import ActivityDraft, SymbolBrief
from src.symbols import library
from src.symbols.profile import profile_for

#: Conditions the pack list reacts to. Keywords come from the locale, so a
#: Hebrew workbook matches Hebrew weather text — see ``packing.<condition>_keywords``.
_CONDITIONS = ("hot", "cold", "rain", "hike", "water", "night", "wildlife")

#: The subset of ``_CONDITIONS`` with a real climate-vocab counterpart
#: (``src/symbols/vocab.py``), letting a matched condition pull from the
#: library's ``pack``-role symbols instead of a fixed list.
_CLIMATE_BY_CONDITION = {"hot": "hot", "cold": "cold", "rain": "wet"}

#: A condition with no climate of its own still names a symbol directly —
#: binoculars for wildlife-watching, hiking shoes for a trek — subject to the
#: same environment veto as everything else.
_CONDITION_SYMBOL_KEYS = {"hike": ("hiking-shoes",), "wildlife": ("binoculars",)}

#: Hot and cold are the one pair of conditions a child can reason about
#: directly ("it's the desert, so no winter coat") — wet has no true
#: opposite, so it never generates a distractor.
_OPPOSITE_CLIMATE = {"hot": "cold", "cold": "hot"}

_PACK_COUNT = {"easy": 5, "medium": 6, "hard": 7}
_DISTRACTOR_COUNT = {"easy": 2, "medium": 3, "hard": 3}

_BACKPACK_KEY = "backpack"


@register_activity
class PackingActivity(ActivityGenerator):
    """A backpack the child fills by drawing lines, not ticking boxes."""

    activity_type = "packing"
    display_name = "Pack the Bag"
    educational_goal = (
        "Introduces planning and cause-and-effect: what the weather and the "
        "activities mean for what you carry — and practises telling a good "
        "idea from a bad one, not just following a list."
    )
    min_age = 4
    max_age = 12
    weight = 12
    energy = "calm"

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        strings = self.strings(context)
        haystack = " ".join(
            [
                *context.knowledge.get("weather"),
                *context.knowledge.get("activities"),
                *context.interests,
                *context.trip.itinerary,
            ]
        ).lower()

        matched = [
            condition
            for condition in _CONDITIONS
            if any(
                keyword.lower() in haystack
                for keyword in strings.items(f"packing.{condition}_keywords")
            )
        ]
        climates = {_CLIMATE_BY_CONDITION[c] for c in matched if c in _CLIMATE_BY_CONDITION}
        profile = profile_for(context.knowledge)

        pack_count = _PACK_COUNT[planned.difficulty]
        pack_symbols = self._pack_symbols(matched, profile)[:pack_count]
        pack_keys = {symbol.key for symbol in pack_symbols}

        distractor_count = _DISTRACTOR_COUNT[planned.difficulty]
        distractor_symbols = self._distractor_symbols(
            context, planned, climates, pack_keys
        )[:distractor_count]

        ring = [*pack_symbols, *distractor_symbols]
        context.rng_for(f"packing:order:{planned.number}").shuffle(ring)

        backpack = library()[_BACKPACK_KEY]

        return self.draft(
            title=self.text(context, "packing.title"),
            instructions=self.text(
                context, "packing.instructions", destination=context.display_destination
            ),
            planned=planned,
            symbols=(
                SymbolBrief(key=backpack.key, label=self._label(context, backpack), subject=backpack.subject),
                *(
                    SymbolBrief(key=s.key, label=self._label(context, s), subject=s.subject)
                    for s in ring
                ),
            ),
            metadata={
                "backpack_key": backpack.key,
                "ring_keys": [s.key for s in ring],
                "pack_keys": sorted(pack_keys),
                "distractor_keys": sorted(symbol.key for symbol in distractor_symbols),
                "items": [self._label(context, s) for s in pack_symbols],
                "not_to_pack": [self._label(context, s) for s in distractor_symbols],
                "blank_slots": 1,
                "matched_conditions": matched,
                #: The hub and ring are typeset entirely from ``symbols`` above —
                #: the page carries no illustration of its own.
                "needs_illustration": False,
            },
        )

    # -- internals ---------------------------------------------------------

    def _label(self, context: WorkbookContext, symbol: Symbol) -> str:
        """The reader-facing name for a symbol, in the workbook's language.

        Nothing on the printed page is labelled — this is for ``workbook.md``,
        the JSON and the answer key only.
        """
        return self.strings(context).optional(f"symbol.{symbol.key}", symbol.label)

    def _pack_symbols(self, matched: list[str], profile) -> list[Symbol]:
        """The library's ``pack``-role symbols to offer, matched conditions first.

        A symbol whose ``environments`` the destination's own profile doesn't
        share is vetoed regardless of climate — skis belong to a snowy
        destination, not merely a cold one. Ordering (rather than random
        sampling) is what guarantees a hot trip actually offers sunscreen
        instead of a random subset of the whole ``pack`` pool; climate-free
        gear (sunglasses, a water bottle) is always a sensible last resort,
        appended after everything condition-specific.
        """
        lib = library()
        ready = [
            symbol
            for symbol in lib.all()
            if symbol.facets is not None
            and symbol.facets.status == "ready"
            and "pack" in symbol.facets.roles
        ]

        def env_ok(symbol: Symbol) -> bool:
            environments = symbol.facets.environments
            return not environments or set(environments) & set(profile.environments)

        ordered: list[Symbol] = []
        seen: set[str] = set()

        def offer(symbol: Symbol) -> None:
            if symbol.key not in seen and env_ok(symbol):
                seen.add(symbol.key)
                ordered.append(symbol)

        for condition in matched:
            climate = _CLIMATE_BY_CONDITION.get(condition)
            if climate:
                for symbol in ready:
                    if climate in symbol.facets.climate:
                        offer(symbol)
            for key in _CONDITION_SYMBOL_KEYS.get(condition, ()):
                if key in lib:
                    offer(lib[key])

        # Climate-agnostic gear (sunglasses, a water bottle, ...) always
        # makes sense to bring, so it tops up any trip that hasn't already
        # filled its quota from something more specific.
        for symbol in ready:
            if not symbol.facets.climate:
                offer(symbol)

        # Last resort so a page never comes up short of items: whatever else
        # the library has, terrain notwithstanding.
        for symbol in ready:
            offer(symbol)

        return ordered

    def _distractor_symbols(
        self,
        context: WorkbookContext,
        planned: PlannedPage,
        climates: set[str],
        pack_keys: set[str],
    ) -> tuple[Symbol, ...]:
        """A few things that would be a mistake to pack for *this* trip.

        Preference goes to the library's own ``pack``-role gear for the
        opposite climate — a real, concrete "why not" (a winter coat doesn't
        belong on a desert trip) rather than an arbitrary wrong answer. A
        trip that matched neither hot nor cold treats both as fair game, and
        if the climate pool still comes up short, everyday non-gear symbols
        (a bicycle, an ice cream — obviously not something you'd pack) fill
        the rest.
        """
        lib = library()
        # A trip that matched *both* hot and cold (a desert's cold nights,
        # say) needs both — neither is a wrong answer, so no climate-based
        # distractor applies and the silly pool below carries the page. Only
        # a trip that named neither falls back to treating both as fair
        # game: with no signal either way, either extreme is a plausible
        # "why would you bring that?" for a child to reason about.
        if climates & {"hot", "cold"}:
            wrong_climates = {
                _OPPOSITE_CLIMATE[climate]
                for climate in climates
                if climate in _OPPOSITE_CLIMATE and _OPPOSITE_CLIMATE[climate] not in climates
            }
        else:
            wrong_climates = {"hot", "cold"}

        mismatched = tuple(
            symbol
            for symbol in lib.all()
            if symbol.facets is not None
            and symbol.facets.status == "ready"
            and "pack" in symbol.facets.roles
            and symbol.key not in pack_keys
            and set(symbol.facets.climate) & wrong_climates
        )

        count = _DISTRACTOR_COUNT[planned.difficulty]
        key = f"packing:distractors:{planned.number}"
        chosen = list(_sample(context, mismatched, count, f"{key}:climate"))

        remaining = count - len(chosen)
        if remaining > 0:
            excluded = pack_keys | {symbol.key for symbol in chosen}
            # This used to be a topic *exclude* list over ``UNIVERSAL_SYMBOLS``
            # (drop "gear" — a real answer, not a silly one — and
            # "animals"/"vehicles", which read as "sort objects from animals"
            # rather than "would you really pack this?"). That still let
            # through "buildings" (fountain, bridge, ...), "street", "nature"
            # (mountain, campfire, ...), "water" and "people" — none of them
            # portable, packable-scale objects — and a live Pelion book
            # shipped exactly that: a fountain and a bridge offered as things
            # *not* to pack, which fails the page's actual test ("would a
            # child mistakenly think to pack this?") by not being a
            # plausible packing candidate in the first place.
            #
            # An allow-list of just "food" is the conservative fix: every
            # entry is small, portable and obviously wrong to pack (it'd
            # melt or spoil), at the cost of dropping "nature" entries that
            # were *also* genuinely portable (chestnuts, olives, grapes)
            # along with the landscape ones. Revisit with a hand-curated
            # mixed-topic allowlist if this pool ever proves too small in
            # practice.
            #
            # Deliberately queries the whole library, not ``UNIVERSAL_SYMBOLS``
            # — that pool is filtered to "everywhere"/"common" ubiquity, which
            # answers "can a child find this on any trip?", not the question
            # that matters here ("is this a small, portable, obviously-wrong
            # thing to pack?"). Restricting to it left only 2 food items
            # (ice-cream, honey) instead of the full 5 (souvlaki, pasta and
            # pomegranate are "local"/"regional") — confirmed too few in
            # practice: a live check across every curated destination pack
            # showed "hard" packing pages (wants 3 distractors) consistently
            # falling short at 2 whenever a trip matches *both* hot and cold
            # (a desert's cold nights, say — Kfar Hanokdim, Pelion), because
            # that leaves the climate-mismatch pool empty and the silly pool
            # has to carry the whole count on its own.
            silly = tuple(
                symbol
                for symbol in lib.all()
                if symbol.facets is not None
                and symbol.facets.status == "ready"
                and symbol.facets.topic in ("food",)
                and symbol.key not in excluded
            )
            chosen.extend(_sample(context, silly, remaining, f"{key}:silly"))

        return tuple(chosen)


def _sample(
    context: WorkbookContext, pool: tuple[Symbol, ...], count: int, key: str
) -> list[Symbol]:
    """Deterministically take ``count`` symbols from ``pool``.

    ``context.sample`` works on strings, so this samples the keys and maps
    back, keeping every random choice on the seeded RNG the whole project
    relies on for reproducible output.
    """
    if count <= 0 or not pool:
        return []
    by_key = {symbol.key: symbol for symbol in pool}
    picked = context.sample(tuple(by_key), min(count, len(by_key)), key=key)
    return [by_key[symbol_key] for symbol_key in picked]
