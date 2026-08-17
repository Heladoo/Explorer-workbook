"""Matching Game: join each drawing to its own shadow.

Shadows rather than words, so the working area stays wordless and the page
works for pre-readers in any language.

The page is built the same way the scavenger hunt is, and for the same reason:
it asks for one small drawing per item (a :class:`SymbolBrief` each) and lets
the print layout place them, instead of asking one prompt for "six animals on
the left and their silhouettes on the right, in a different order". That prompt
fails on exactly the things the puzzle needs — the shadow has to be the *same*
shape at the *same* size as its partner, and the two columns have to disagree
about the order. Deriving both columns from one drawing (see
``tools/make_shadow_symbols.py``) makes those guarantees arithmetic rather than
hopeful.

Items come from the universal symbol bank rather than from the destination's
own wildlife and landmarks. A shadow puzzle is a shape-recognition exercise,
not a geography one, and the universal pool is the part of the symbol cache
that has artwork committed for it in every book — a destination sight that has
never been drawn would print as a placeholder in the left column and, worse, as
a *blank* in the shadow column.

"Universal" is about artwork coverage, not about fitting every destination,
though — a handful of the pool's ``pack``-adjacent items (a woolly hat, a
rain coat) carry real ``environments``/``climate`` facets, and a woolly hat
still reads as wrong for a warm-climate trip even though the *shape* puzzle
itself has nothing to do with weather. ``_choose`` prefers symbols whose
facets fit the destination's profile (the same veto ``packing.py`` already
applies to its own pool) and only falls back to the unfiltered bank if too
few fit — the page must never come up short of pairs over this.
"""

from __future__ import annotations

from src.activities._symbols import UNIVERSAL_SYMBOLS, Symbol
from src.activities.base import (
    ActivityGenerator,
    PlannedPage,
    register_activity,
)
from src.models.context import DestinationProfile, WorkbookContext
from src.models.page import ActivityDraft, SymbolBrief
from src.symbols.profile import profile_for

#: Pairs per page. Kept to 5-6 regardless of difficulty: every pair is a
#: full-height row in both columns, so fewer than five leaves the page looking
#: sparse, and past six the drawings print too small to tell apart by outline
#: alone — which is the whole skill the page is training.
_PAIR_COUNT = {"easy": 5, "medium": 5, "hard": 6}

#: Universal-pool keys excluded from the matching page only. The scavenger
#: hunt shows these symbols as their full cutout, where the drawing carries
#: interior detail; the matching page reduces the same shape to a solid
#: silhouette, and for these the resulting outline was rejected on review —
#: not distinct/recognisable enough as a shape alone, even after
#: `tools/make_shadow_symbols.py` derives a correct silhouette for them.
#: The rejected `silhouettes/<key>.png` files themselves were deleted rather
#: than left on disk unused — do not regenerate them for these keys; a
#: shape that didn't read as its subject the first time won't on a rerun.
#: (`water-bottle` was here too, but its silhouette turned out fine once the
#: cutout's frame-detection bug — see `FORCE_STRIP_FRAME` in
#: `tools/make_shadow_symbols.py` — was fixed; both files were regenerated.)
_SHADOW_UNSUITABLE = {"train", "tractor", "sunscreen"}


@register_activity
class MatchingActivity(ActivityGenerator):
    """Shape recognition over everyday things and their silhouettes."""

    activity_type = "matching"
    display_name = "Matching Game"
    educational_goal = (
        "Trains shape recognition and one-to-one correspondence by matching each "
        "subject to its silhouette."
    )
    min_age = 3
    max_age = 9
    weight = 12
    energy = "active"
    # Raised above the default of 1 for the same reason maze's is (see its
    # own comment: enough active-energy supply to alternate against calm
    # pages now that hidden_objects/spot_difference are paused). Kept at 2
    # rather than maze's higher ceiling — its shadow-matching set draws from
    # a shared universal symbol pool, so a repeat wears thinner sooner than a
    # maze's freshly carved layout does.
    max_per_workbook = 2

    def supports(self, context: WorkbookContext) -> bool:
        # Like the scavenger hunt, this page is built from the universal symbol
        # bank, so it needs no destination knowledge at all.
        return super().supports(context)

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        count = _PAIR_COUNT[planned.difficulty]
        subjects = self._choose(context, planned, count)

        # The right-hand column holds the same set in a different order —
        # shuffled explicitly, because sampling every element of a pool returns
        # it unchanged and would let the child match straight across.
        shadow_order = list(subjects)
        context.rng_for(f"matching:shadows:{planned.number}").shuffle(shadow_order)
        if len(shadow_order) > 1 and shadow_order == list(subjects):
            shadow_order.append(shadow_order.pop(0))

        labels = [self._label(context, symbol) for symbol in subjects]
        keys = [symbol.key for symbol in subjects]
        shadow_keys = [symbol.key for symbol in shadow_order]

        return self.draft(
            title=self.text(context, "matching.title"),
            instructions=self.text(
                context, "matching.instructions", kind=self.text(context, "common.kind_picture")
            ),
            planned=planned,
            symbols=tuple(
                SymbolBrief(
                    key=symbol.key,
                    label=self._label(context, symbol),
                    subject=symbol.subject,
                    universal=symbol.universal,
                )
                for symbol in subjects
            ),
            metadata={
                "pair_count": len(subjects),
                "left_column": labels,
                "right_column": [self._label(context, symbol) for symbol in shadow_order],
                "symbol_keys": keys,
                #: Read by the print layout to order the shadow column; the
                #: labels above are for ``workbook.md`` and the JSON, which are
                #: localized and so cannot be matched back to a drawing.
                "shadow_keys": shadow_keys,
                "answer_key": {
                    label: shadow_keys.index(key) + 1 for label, key in zip(labels, keys)
                },
                #: The two columns are typeset entirely from ``symbols`` above —
                #: the page carries no illustration of its own.
                "needs_illustration": False,
            },
        )

    # -- internals -------------------------------------------------------

    def _label(self, context: WorkbookContext, symbol: Symbol) -> str:
        """What the answer key calls this thing, in the workbook's language.

        Nothing on the printed working area is labelled — the label exists for
        ``workbook.md``, the JSON and the answer key.
        """
        if not symbol.universal:
            return symbol.label
        return self.strings(context).optional(f"symbol.{symbol.key}", symbol.label)

    def _choose(
        self, context: WorkbookContext, planned: PlannedPage, count: int
    ) -> tuple[Symbol, ...]:
        """Deterministically take ``count`` symbols from the universal bank.

        ``context.sample`` works on strings, so this samples keys and maps back,
        keeping every random choice on the seeded RNG the whole project relies
        on for reproducible output.

        Prefers symbols that fit the destination's profile (see the module
        docstring); the unfiltered bank is a fallback only reached when the
        fitting pool alone can't fill ``count`` — most of the 38-symbol
        universal pool carries no environment/climate facet at all, so this
        should only bite for a destination whose profile itself is unusually
        sparse.
        """
        by_key = {
            symbol.key: symbol
            for symbol in UNIVERSAL_SYMBOLS
            if symbol.key not in _SHADOW_UNSUITABLE
        }
        profile = profile_for(context.knowledge)
        fitting = tuple(key for key in by_key if _fits(by_key[key], profile))
        pool_keys = fitting if len(fitting) >= count else tuple(by_key)
        picked = context.sample(
            pool_keys, min(count, len(pool_keys)), key=f"matching:{planned.number}"
        )
        return tuple(by_key[key] for key in picked)


def _fits(symbol: Symbol, profile: DestinationProfile) -> bool:
    """Whether ``symbol``'s facets don't rule out this destination.

    Only vetoes on a facet the symbol actually declares — an empty
    ``environments``/``climate`` means "findable/relevant anywhere" (see
    ``SymbolFacets``), so most of the pool always passes. A woolly hat
    (``climate=("cold",)``) is vetoed for a destination profiled
    ``("temperate", "hot")``, same principle as ``packing.py``'s own
    environment veto for its ``pack``-role symbols.
    """
    environments = symbol.facets.environments
    if environments and not set(environments) & set(profile.environments):
        return False
    climate = symbol.facets.climate
    if climate and not set(climate) & set(profile.climate):
        return False
    return True
