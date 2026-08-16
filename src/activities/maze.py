"""Maze: a real spanning-tree maze from home to a real place on the trip.

The maze is generated in Python (see ``src/activities/_maze.py``) and
typeset directly from its wall data by ``@layout("maze")`` — never drawn by
an image model, the one thing an image model cannot be trusted to get right
("exactly one path, no dead end near the exit"). The page carries no
page-level illustration at all; the only artwork is two small cached icons
marking the start and the goal.
"""

from __future__ import annotations

from src.activities._maze import NORTH, SOUTH, generate_maze, grid_for, open_boundary
from src.activities._symbols import _LATIN, _match_alias, _topic
from src.activities.base import (
    ActivityGenerator,
    PlannedPage,
    SymbolBrief,
    register_activity,
)
from src.models.context import WorkbookContext, slugify
from src.models.page import ActivityDraft
from src.symbols import Symbol, library
from src.symbols.profile import profile_for

#: Which shared library icon reads as "you've arrived", by the destination's
#: own environment — checked in this order so a place matching more than one
#: (a mountain village) still gets a single, sensible pick. A fixed, cached
#: drawing instead of a fresh flag-plus-topic illustration minted per book
#: means every goal marker is already real artwork, never a placeholder.
#: Used only as the *generic* fallback now (see ``MazeActivity._goal``) — a
#: real landmark that resolves to a real symbol always wins over this.
_GOAL_ICON_BY_ENVIRONMENT: tuple[tuple[str, str], ...] = (
    ("mountain", "mountain"),
    ("village", "village"),
    ("water", "boat"),
    ("coast", "boat"),
)
#: No environment hint at all (a city, or an unprofiled destination) still
#: needs an icon — a fountain reads as "arrived somewhere" the way the
#: airplane start icon reads as "off on a trip", without claiming any
#: particular terrain. Also the last resort when every environment-matched
#: icon above has already been used by an earlier maze in the same book.
_DEFAULT_GOAL_ICON = "fountain"

#: A book can carry more than one maze (``max_per_workbook`` above allows up
#: to 3) — a second or third maze needs its own start icon, or it reads as a
#: duplicate of the first. Indexed by ``occurrence - 2`` (occurrence 1 is the
#: trip-opening airplane, handled separately) and clamped to the last entry
#: so a future ``max_per_workbook`` bump degrades gracefully instead of
#: raising. All three already have committed cutout art.
_REPEAT_START_ICONS: tuple[str, ...] = ("dog", "bicycle", "truck")


@register_activity
class MazeActivity(ActivityGenerator):
    """A path puzzle whose finish is a real place the family will actually see."""

    activity_type = "maze"
    display_name = "Maze"
    educational_goal = (
        "Practises visual planning, sequencing and pencil control, and links "
        "the trip to one real place the family will actually see."
    )
    min_age = 4
    max_age = 11
    weight = 18
    energy = "active"
    # Raised so the book has enough active-energy supply to alternate against
    # calm pages now that hidden_objects/spot_difference are paused (see their
    # `enabled = False`) — with only 3 active activity types left, capping
    # each at 1 left books tailing off into a long run of calm pages.
    max_per_workbook = 3

    def generate(self, context: WorkbookContext, planned: PlannedPage) -> ActivityDraft:
        hero = self.hero(context)
        strings = self.strings(context)

        # Which icon prints as the start marker (see below) is known before
        # the instructions are worded, so the wording can name it correctly
        # instead of a fixed "home" regardless of which icon actually shows.
        occurrence = int(planned.metadata.get("occurrence", 1))
        start_key = (
            "airplane"
            if occurrence < 2
            else _REPEAT_START_ICONS[min(occurrence - 2, len(_REPEAT_START_ICONS) - 1)]
        )
        start_label = self._start_label(context, start_key)

        # The goal's text and its icon are resolved together (see ``_goal``)
        # so they can never disagree — worded into the instructions only
        # once both are settled.
        goal, goal_symbol = self._goal(context, planned, occurrence)
        instructions = self.text(
            context, "maze.instructions", hero=hero, start=start_label, goal=goal
        )

        columns, rows = grid_for(planned.difficulty)
        rng = context.rng_for(f"maze:grid:{planned.number}")
        maze = generate_maze(rng, columns, rows)

        # The maze itself is direction-agnostic; only where the reader's eye
        # naturally enters the page changes with the language. Start is
        # always the top row, goal always the bottom row — only which column
        # moves — so the doorway sides below (NORTH/SOUTH) never change.
        if strings.is_rtl:
            start_cell = (0, columns - 1)
            goal_cell = (rows - 1, 0)
        else:
            start_cell = (0, 0)
            goal_cell = (rows - 1, columns - 1)

        # A freshly carved maze is a fully closed rectangle — every cell on
        # the edge keeps its outward wall. Knock down just the start and goal
        # cells' outward walls so each has one real doorway off the sheet,
        # for the start/goal boxes the layout draws just outside the grid.
        maze = open_boundary(maze, *start_cell, NORTH)
        maze = open_boundary(maze, *goal_cell, SOUTH)

        # The first maze in the book gets the generic "you're off on your
        # trip" marker — the same airplane symbol the scavenger hunt can
        # draw, generated once and reused in every book, in every language.
        # Looked up here rather than at import time (as a bare ``next()``
        # over the pool used to) so a malformed library fails a book at
        # generation, not the whole activity registry at discovery;
        # ``vocab.REQUIRED_KEYS`` pins "airplane" so this lookup is
        # guaranteed to succeed for any library that loads at all. A second
        # or later maze gets a fixed, different icon instead (see
        # ``_REPEAT_START_ICONS``). ``occurrence``/``start_key`` themselves
        # are resolved above, before the instructions are worded.
        start_symbol = SymbolBrief(
            key=start_key, label=start_label, subject=library().subject(start_key)
        )

        return self.draft(
            title=self.text(context, "maze.title", goal=goal),
            instructions=instructions,
            planned=planned,
            metadata={
                "start": start_label,
                "goal": goal,
                "needs_illustration": False,
                "grid": {
                    "columns": columns,
                    "rows": rows,
                    "walls": [list(row) for row in maze.walls],
                    "start_cell": list(start_cell),
                    "goal_cell": list(goal_cell),
                },
                "symbol_keys": [start_symbol.key, goal_symbol.key],
            },
            symbols=(start_symbol, goal_symbol),
        )

    def _start_label(self, context: WorkbookContext, start_key: str) -> str:
        """The instructions' start phrase, matched to the icon actually drawn.

        ``maze.start_label`` used to be a fixed "home"/"הבית" regardless of
        which icon the page actually printed — an airplane for the first
        maze in a book, the fixed ``_REPEAT_START_ICONS`` for a later one,
        never a house — so the instructions and the picture disagreed (a
        live Pelion/he run said "מהבית" while the icon was an airplane, then
        a dog). ``maze.start_label.<key>`` gives each icon its own natural
        phrase; an icon with no entry falls back to the old generic one.
        """
        return self.strings(context).optional(
            f"maze.start_label.{start_key}", self.text(context, "maze.start_label")
        )

    def _goal(
        self, context: WorkbookContext, planned: PlannedPage, occurrence: int
    ) -> tuple[str, SymbolBrief]:
        """The goal's text and its icon, resolved together so they agree.

        ``goal`` used to be a real landmark name (``self.pick(..., "landmarks",
        1)``) while the printed icon was picked independently, purely from the
        destination's environment (``_GOAL_ICON_BY_ENVIRONMENT``) — the two
        had no connection at all. A live Pelion/he run showed the instructions
        naming "רכבת הקיטור העתיקה של פליון" (the old steam train) while the
        icon printed was a generic mountain.

        This tries every landmark, not just the first ``pick()`` would have
        returned, for one whose own concept happens to coincide with a real,
        ``ready`` library symbol — reusing the exact alias/topic-matching
        ``destination_symbols()`` already does for ``wildlife``/``plants``/
        ``local_food`` (see ``_symbols.py``; ``landmarks`` is deliberately
        excluded from *that* pool because a place name isn't a generic
        "thing to spot" — this is a narrower use, only checking whether a
        landmark's concept happens to already have a drawable icon). A
        ``ready`` match is guaranteed committed cutout art (see the comment
        at ``_symbols.py`` ~line 158), so no separate art check is needed.

        A book's mazes must not repeat a goal, and activities can't share
        state across ``generate()`` calls (see CLAUDE.md) — so this was
        first tried keying the shuffle to ``planned.number`` (which differs
        per page) and trusting that alone to spread occurrences across
        different landmarks. A live check against the Pelion pack (8
        landmarks, only the 2 "village of ..." ones resolving to a real
        symbol, both to the *same* "village" icon) showed that guess wrong:
        3 of 4 seeds tried landed occurrence 1 and 2 on the same landmark.
        Keying the shuffle to the *book* instead (no ``planned.number``) —
        so every maze page in the same book computes the identical ordered
        match list — fixes it precisely: occurrence N always takes the Nth
        *distinct-icon* match, so occurrence 1 and 2 provably never agree
        as long as two matches exist at all.
        """
        lib = library()
        ready_symbols = tuple(
            symbol
            for symbol in lib.all()
            if symbol.facets is not None and symbol.facets.status == "ready"
        )
        english_terms = context.knowledge.english_terms
        landmarks = list(context.knowledge.get("landmarks") or ())
        context.rng_for("maze:goal-order").shuffle(landmarks)

        matches: list[tuple[str, Symbol]] = []
        seen_keys: set[str] = set()
        for landmark in landmarks:
            english = english_terms.get(landmark, landmark)
            # Same guard ``destination_symbols()`` uses: an untranslated
            # non-Latin phrase has no English form to shorten or slugify.
            if not _LATIN.search(english):
                continue
            topic = _topic(english)
            key = slugify(topic)
            symbol: Symbol | None = lib[key] if key in lib else None
            if symbol is None or symbol.facets.status != "ready":
                symbol = _match_alias(topic, ready_symbols)
            # Two differently-worded landmarks can resolve to the same icon
            # (Pelion's two villages both land on "village") — keep only the
            # first so a later occurrence never gets offered a duplicate
            # icon under a different landmark name.
            if symbol is not None and symbol.key not in seen_keys:
                seen_keys.add(symbol.key)
                matches.append((landmark, symbol))

        index = occurrence - 1
        if index < len(matches):
            landmark, symbol = matches[index]
            return landmark, SymbolBrief(key=symbol.key, label=landmark, subject=symbol.subject)

        # Landmarks ran out before this occurrence — printing one anyway
        # would draw a mismatched or unmatched icon (or, worse, a raw
        # English slug with nothing to illustrate it at all). Fall back to a
        # generic destination, excluding whatever icon(s) an earlier
        # occurrence already claimed above.
        #
        # ``rank`` — not the raw ``occurrence`` — indexes the generic
        # candidate list: occurrence 1 can consume a landmark match without
        # ever touching the generic pool, so occurrence 2 and 3 both falling
        # through here are the *1st* and *2nd* generic fallback respectively,
        # not the "2nd" and "3rd" as ``occurrence`` alone would suggest.
        # Using ``occurrence`` directly here was tried first and failed a
        # concrete case: 1 landmark match + 2 generic fallbacks both indexed
        # by raw occurrence (2 and 3) landed on the same clamped last
        # candidate — see ``test_three_mazes_in_one_book_never_repeat_a_start_or_goal``.
        rank = occurrence - 1 - len(matches)
        return self._generic_goal(context, planned, rank, seen_keys)

    def _generic_goal(
        self,
        context: WorkbookContext,
        planned: PlannedPage,
        rank: int,
        claimed: frozenset[str] = frozenset(),
    ) -> tuple[str, SymbolBrief]:
        """A generic, environment-appropriate goal when no landmark matched.

        Environment matches are ordered by ``_GOAL_ICON_BY_ENVIRONMENT`` and
        de-duplicated (a mountain village matches both "mountain" and
        "village", but should only ever offer each icon once); the fixed
        ``_DEFAULT_GOAL_ICON`` is appended as the last resort. ``claimed`` —
        the icon keys ``_goal`` already matched to an earlier occurrence's
        landmark, in this same call — is filtered out too, so a second maze
        whose own landmarks ran out doesn't fall back to the exact icon a
        first maze's landmark match already used. Indexing what's left by
        ``rank`` — the 0-based count of *earlier* occurrences that also fell
        back to this generic pool, computed by the caller — rather than
        always taking the first match, as a single-maze book always did,
        means a second or third maze that *also* has nothing left to match
        still gets a different generic icon from the first, instead of
        repeating it (the old, cruder fix for this was a single hardcoded
        ``_REPEAT_GOAL_ICON = "fountain"`` for every repeat maze, with no
        reference to the goal text at all).

        The generic pool is small (at most 4 keys after de-duplication), so
        this still degrades to a repeat once ``rank`` outruns however
        many distinct candidates are left — only reachable via the planner's
        own ``cap_bonus`` escape valve for a book long enough to exceed
        ``max_per_workbook`` on every activity type at once (confirmed with
        a 40-page Pelion book, 5 mazes deep — the ordinary range this
        project actually ships stays well under that). Never a crash either
        way: ``or all_candidates`` below guarantees ``candidates`` is never
        empty even if every entry were somehow claimed.

        The icon's own bare label ("a mountain"/"הר") is wrapped with the
        destination name rather than printed alone —
        ``test_activities_are_destination_aware`` requires every activity's
        text to name the destination or something from its knowledge, and a
        generic icon label alone names neither. "near {destination}" keeps
        text and icon in agreement (both are still just "a mountain") while
        keeping the page honestly about *this* trip, the same job the
        landmark name was doing before it turned out not to match anything.
        """
        profile = profile_for(context.knowledge)
        matches = [icon for env, icon in _GOAL_ICON_BY_ENVIRONMENT if env in profile.environments]
        all_candidates = list(dict.fromkeys(matches))
        if _DEFAULT_GOAL_ICON not in all_candidates:
            all_candidates.append(_DEFAULT_GOAL_ICON)
        candidates = [c for c in all_candidates if c not in claimed] or all_candidates
        key = candidates[min(max(rank, 0), len(candidates) - 1)]
        symbol = library()[key]
        subject = self.strings(context).optional(f"symbol.{key}", symbol.label)
        label = self.text(
            context, "maze.goal_fallback", subject=subject, destination=context.display_destination
        )
        return label, SymbolBrief(key=symbol.key, label=label, subject=symbol.subject)
