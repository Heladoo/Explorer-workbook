"""Page layouts for print.

One builder per activity type, registered by name. An activity with no
registered layout falls back to a full-page illustration frame, so a new
activity plugin prints correctly without anyone touching this module; giving
it a bespoke layout later means adding one function and one template.

The layouts turn the page metadata the activities recorded — checkbox counts,
quiz options, matching columns, star counts — into real page furniture. That
is why none of it is baked into the illustration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.activities._maze import Maze, wall_segments
from src.models.context import WorkbookContext
from src.models.page import Page, SymbolBrief
from src.rendering.templates import TemplateSet, esc
from src.strings import Strings

#: Rendered markup for the working area of one page.
LayoutBuilder = Callable[["LayoutContext", Page], str]

LAYOUTS: dict[str, LayoutBuilder] = {}


def layout(*activity_types: str) -> Callable[[LayoutBuilder], LayoutBuilder]:
    """Register a builder for one or more activity types."""

    def register(builder: LayoutBuilder) -> LayoutBuilder:
        for activity_type in activity_types:
            LAYOUTS[activity_type] = builder
        return builder

    return register


@dataclass(frozen=True)
class LayoutContext:
    """What a layout builder is given."""

    templates: TemplateSet
    context: WorkbookContext
    strings: Strings
    images: dict[int, str]
    #: Per-symbol artwork, keyed by symbol slug rather than page number — the
    #: same stop sign serves every page and every book that asks for one.
    symbol_images: dict[str, str] = field(default_factory=dict)
    #: The same drawings with their paper and rule removed, and filled solid as
    #: shadows. Derived offline by ``tools/make_shadow_symbols.py``; see
    #: :mod:`src.symbol_art`.
    symbol_cutouts: dict[str, str] = field(default_factory=dict)
    symbol_shadows: dict[str, str] = field(default_factory=dict)

    def symbol_art(self, symbol: SymbolBrief) -> str:
        """One grid cell's picture: the real drawing, or an empty box."""
        source = self.symbol_images.get(symbol.key)
        if source:
            return self.templates.render("art_symbol", src=source, label=symbol.label)
        return self.templates.render("art_symbol_placeholder", reference=symbol.key)

    def symbol_cutout_art(self, symbol: SymbolBrief) -> str:
        """The borderless cut-out for a symbol, falling back to the framed
        drawing and then the placeholder.

        Used where a single small icon sits directly on the page background
        (the maze's start marker) rather than in a ruled grid cell, so a
        ruled square around it would look like a stray box rather than page
        furniture.
        """
        source = self.symbol_cutouts.get(symbol.key)
        if source:
            return self.templates.render("art_symbol", src=source, label=symbol.label)
        return self.symbol_art(symbol)

    def art(self, page: Page, *, label: str | None = None, note: str | None = None) -> str:
        """The illustration area: the real image when there is one, else a frame."""
        source = self.images.get(page.number)
        if source:
            return self.templates.render("art_image", src=source, label=page.title)
        # No prompt was ever generated for a page with no brief, so there is
        # nothing to point the reference line at.
        reference = f"prompts/{page.prompt_filename}" if page.image_brief is not None else ""
        return self.templates.render(
            "art",
            label=label or self.strings.text("pdf.illustration"),
            reference=reference,
            note=note or self.strings.text("pdf.art_note"),
        )

    def text(self, key: str, **kwargs: str) -> str:
        return self.strings.text(key, **kwargs)

    def logo(self) -> str:
        """The Adventure Kit mark, inlined so the printed HTML stays
        self-contained — empty string if the asset isn't shipped."""
        uri = self.templates.asset_data_uri("assets/logo-bw.png", "image/png")
        if not uri:
            return ""
        return f'<img class="brand-logo" src="{uri}" alt="Adventure Kit">'


def build_body(layout_context: LayoutContext, page: Page) -> str:
    """Render the working area for ``page`` using its registered layout."""
    builder = LAYOUTS.get(page.type, _default_layout)
    return builder(layout_context, page)


def _default_layout(layout_context: LayoutContext, page: Page) -> str:
    return layout_context.templates.render("body_default", art=layout_context.art(page))


@layout("cover")
def _cover(layout_context: LayoutContext, page: Page) -> str:
    return layout_context.templates.render(
        "body_cover",
        art=layout_context.art(page),
        name_label=layout_context.text("pdf.name_label"),
        logo_html=layout_context.logo(),
    )


@layout("drawing")
def _drawing(layout_context: LayoutContext, page: Page) -> str:
    return layout_context.templates.render(
        "body_default",
        art=layout_context.art(page, label=layout_context.text("pdf.draw_here")),
    )


@layout("maze")
def _maze(layout_context: LayoutContext, page: Page) -> str:
    """The corridors are real data, so they are typeset — never drawn.

    A wall path in cell units inside a ``viewBox``-fitted SVG can never push
    the page past its printed height, however big the grid gets — a stronger
    version of the same guarantee ``.spotting`` gets from explicit grid rows.

    The start and goal icons live in their own boxes *outside* the grid
    rectangle, not overlaid on top of a corner cell — the generator (see
    ``MazeActivity.generate``) already knocked a doorway through the start
    cell's north wall and the goal cell's south wall, and each box sits
    flush against that doorway so the walk visibly starts and ends off the
    sheet rather than in a walled-in corner. The box itself is drawn wider
    than the one-cell doorway it opens onto — at the smallest corridor width
    a cell is barely 13mm, too tight to hold a symbol with any breathing
    room — so it reads as a little room the (still exactly cell-width)
    doorway leads into, not a picture squeezed to match the corridor.
    """
    grid = page.metadata.get("grid") or {}
    columns = int(grid.get("columns", 1))
    rows = int(grid.get("rows", 1))
    maze = Maze(columns=columns, rows=rows, walls=tuple(tuple(row) for row in grid.get("walls", ())))
    _, start_col = grid.get("start_cell", [0, 0])
    _, goal_col = grid.get("goal_cell", [rows - 1, columns - 1])

    start_symbol, goal_symbol = page.symbols

    cell = 100 / columns
    box = min(100.0, cell * 1.6)

    def endcap(role: str, col: int, art: str, *, icon_class: str = "") -> str:
        offset = max(0.0, min(100 - box, (col + 0.5) * cell - box / 2))
        return layout_context.templates.render(
            "body_maze_endcap",
            role=role,
            offset=f"{offset:.4f}%",
            width=f"{box:.4f}%",
            art=art,
            icon_class=f" {icon_class}" if icon_class else "",
        )

    return layout_context.templates.render(
        "body_maze",
        columns=columns,
        rows=rows,
        walls=wall_segments(maze),
        # Both markers are always-cached library symbols now (see
        # MazeActivity._goal), so both cut-outs always exist — borderless
        # looks right sitting directly on the page background. The airplane
        # drawing itself is nose-up (see the library entry), so only *that*
        # icon gets flipped — a repeat maze's animal/vehicle start icon
        # (MazeActivity._REPEAT_START_ICONS) must not inherit the same
        # rotation, hence the class is keyed to the symbol, not the role.
        start_endcap=endcap(
            "start",
            start_col,
            layout_context.symbol_cutout_art(start_symbol),
            icon_class="maze-endcap-airplane" if start_symbol.key == "airplane" else "",
        ),
        goal_endcap=endcap("goal", goal_col, layout_context.symbol_cutout_art(goal_symbol)),
    )


@layout("scavenger_hunt")
def _spotting_grid(layout_context: LayoutContext, page: Page) -> str:
    """A table of pictures: one drawing, one checkbox and one label per cell.

    The grid is built here rather than drawn, because a picture of a grid is
    the one thing an image model cannot be trusted to get right — exact cell
    counts, one specific item per cell, and no stray text. Each cell's picture
    comes from its own prompt (``prompts/symbols/<key>.md``), so a cell that
    comes out wrong is one cheap retry rather than a ruined page.
    """
    cells = [
        layout_context.templates.render(
            "body_spotting_cell",
            # The cut-out, not the framed `images/<key>.png` sheet: every
            # cut-out is cropped tight to its own ink (see
            # `tools/make_shadow_symbols.py`), so every cell's artwork ends
            # up the same effective size regardless of how differently the
            # source drawings were originally cropped/padded. The raw framed
            # version varies wildly in canvas size — 1254px square for the
            # original set, but far smaller and non-square for cells cropped
            # straight out of a grid sheet — which the CSS's object-fit box
            # cannot fully absorb and was overflowing the sheet onto the next
            # printed page.
            art=layout_context.symbol_cutout_art(symbol),
            label=symbol.label,
        )
        for symbol in page.symbols
    ]
    return layout_context.templates.render(
        "body_spotting",
        columns=int(page.metadata.get("columns", 4)),
        rows=int(page.metadata.get("rows", 4)),
        cells="\n".join(cells),
    )


@layout("hidden_objects")
def _checklist(layout_context: LayoutContext, page: Page) -> str:
    items = list(page.metadata.get("items") or page.metadata.get("objects") or ())
    cells = [
        layout_context.templates.render("body_checklist_item", item_class="", label=item)
        for item in items
    ]
    for _ in range(int(page.metadata.get("blank_slots", 0))):
        cells.append(
            layout_context.templates.render(
                "body_checklist_item",
                item_class="blank",
                label=layout_context.text("pdf.your_own"),
            )
        )
    return layout_context.templates.render(
        "body_checklist", art=layout_context.art(page), items="\n".join(cells)
    )


@layout("packing")
def _packing(layout_context: LayoutContext, page: Page) -> str:
    """A backpack at the hub, everything else drawn in a ring around it.

    A classic CSS "clock face" placement (rotate to the item's angle,
    translate outward, counter-rotate the art back upright — see
    ``.packing-item`` in book.css) rather than a rectangular grid: any item
    count spaces itself evenly around the full circle with no per-count
    layout table to maintain, and the stage sizes itself in container-query
    units so it can't overflow its sheet regardless of how much room the
    title and instructions above it took (the same technique the word
    search's ``.puzzle-grid`` uses, for the same reason).

    The child draws their own line from each drawing to the backpack — real
    ones and the few that don't belong (``pack_keys`` / ``distractor_keys``
    in the page metadata, for the answer key) look identical here, on
    purpose: telling them apart is the puzzle.
    """
    hub_symbol, *ring_symbols = page.symbols
    blank_slots = int(page.metadata.get("blank_slots", 0))
    total = len(ring_symbols) + blank_slots

    nodes = [
        _packing_node(layout_context, index, total, art=layout_context.symbol_cutout_art(symbol))
        for index, symbol in enumerate(ring_symbols)
    ]
    nodes.extend(
        _packing_node(layout_context, len(ring_symbols) + offset, total, art="", blank=True)
        for offset in range(blank_slots)
    )

    return layout_context.templates.render(
        "body_packing",
        art=layout_context.symbol_cutout_art(hub_symbol),
        nodes="\n".join(nodes),
    )


def _packing_node(
    layout_context: LayoutContext, index: int, total: int, *, art: str, blank: bool = False
) -> str:
    angle = (index / total * 360) if total else 0.0
    return layout_context.templates.render(
        "body_packing_node",
        angle=f"{angle:.2f}deg",
        item_class=" packing-item-blank" if blank else "",
        art=art,
    )


@layout("quiz")
def _quiz(layout_context: LayoutContext, page: Page) -> str:
    """Text-only questions, three lettered options each, sharing the sheet
    with a local-language dictionary when the page has one (see
    ``src/activities/quiz.py`` and ``_dictionary_section`` below).

    Both sections use explicit grid rows (``--quiz-rows`` / ``--dict-rows``
    in book.css) rather than content-sized ones: three short questions and
    ten short dictionary rows are small enough that the real risk on this
    page is content trailing off and leaving the bottom of the sheet blank,
    not overflowing past it — the opposite of most other activity pages.
    """
    alphabet = layout_context.strings.alphabet
    questions = page.metadata.get("questions", ())
    rows = []
    for index, question in enumerate(questions, start=1):
        options = "\n".join(
            layout_context.templates.render(
                "body_quiz_option",
                letter=alphabet[option_index] if option_index < len(alphabet) else "",
                label=option,
            )
            for option_index, option in enumerate(question.get("options", ()))
        )
        rows.append(
            layout_context.templates.render(
                "body_quiz_row",
                number=index,
                question=question.get("question", ""),
                options=options,
            )
        )
    return layout_context.templates.render(
        "body_quiz",
        row_count=len(questions),
        rows="\n".join(rows),
        dictionary=_dictionary_section(layout_context, page),
    )


def _dictionary_section(layout_context: LayoutContext, page: Page) -> str:
    """The quiz page's local-language dictionary, or "" when the destination
    has none (see ``QuizActivity`` — same language as the workbook, no
    curated phrasebook, or no embedded font coverage for its script all
    omit it rather than print a half-empty or broken table)."""
    entries = page.metadata.get("dictionary")
    if not entries:
        return ""
    native_dir = page.metadata.get("native_direction", "ltr")
    native_lang = page.metadata.get("native_language", "")
    rows = "\n".join(
        layout_context.templates.render(
            "body_dictionary_row",
            meaning=entry.get("meaning", ""),
            native=entry.get("native", ""),
            pronunciation=entry.get("pronunciation", ""),
            native_dir=native_dir,
            native_lang=native_lang,
        )
        for entry in entries
    )
    language_name = layout_context.strings.optional(f"language.{native_lang}", native_lang)
    return layout_context.templates.render(
        "body_dictionary",
        title=layout_context.text("dictionary.title"),
        instructions=layout_context.text(
            "dictionary.instructions", count=len(entries), language=language_name
        ),
        row_count=len(entries),
        col_meaning=layout_context.text("dictionary.col_meaning"),
        col_native=layout_context.text("dictionary.col_native"),
        col_say=layout_context.text("dictionary.col_say"),
        entries=rows,
    )


@layout("matching")
def _matching(layout_context: LayoutContext, page: Page) -> str:
    """Two columns of pictures: the drawings on one side, their shadows on the
    other, in a different order.

    Both columns are typeset from the *same* per-symbol drawings the scavenger
    hunt uses, in two variants derived from one crop box — so a picture and its
    shadow are guaranteed the same size and pose, which is the one thing the
    puzzle depends on and the one thing a single generated illustration of "six
    animals and their silhouettes" never gets right.

    The page carries no words inside the working area at all: a pre-reader can
    do it, and it needs no translation.
    """
    by_key = {symbol.key: symbol for symbol in page.symbols}
    shadow_order = [
        by_key[key] for key in page.metadata.get("shadow_keys", ()) if key in by_key
    ]

    def cells(symbols, *lookups: dict[str, str]) -> str:
        return "\n".join(
            layout_context.templates.render(
                "body_matching_cell",
                art_html=_match_art(layout_context, symbol, lookups),
            )
            for symbol in symbols
        )

    return layout_context.templates.render(
        "body_matching",
        # A missing cut-out falls back to the framed original: a ruled box
        # around each drawing looks worse but still solves. The shadow column
        # gets no such fallback — the original *is* the answer.
        left=cells(page.symbols, layout_context.symbol_cutouts, layout_context.symbol_images),
        right=cells(shadow_order, layout_context.symbol_shadows),
        gutter_note=layout_context.text("pdf.match_gutter"),
    )


def _match_art(
    layout_context: LayoutContext, symbol: SymbolBrief, lookups: tuple[dict[str, str], ...]
) -> str:
    """One matching cell's picture from the first lookup that has it, else the
    usual placeholder naming the symbol's prompt key."""
    for sources in lookups:
        source = sources.get(symbol.key)
        if source:
            return layout_context.templates.render(
                "art_match", src=source, label=symbol.label
            )
    return layout_context.templates.render("art_match_placeholder", reference=symbol.key)


@layout("wildlife_facts")
def _cards(layout_context: LayoutContext, page: Page) -> str:
    cards = [
        layout_context.templates.render(
            "body_card",
            art_note=layout_context.text("pdf.illustration"),
            name=card.get("animal", ""),
            caption=card.get("caption", ""),
        )
        for card in page.metadata.get("cards", ())
    ]
    return layout_context.templates.render("body_cards", cards="\n".join(cards))


@layout("reflection")
def _reflection(layout_context: LayoutContext, page: Page) -> str:
    line = layout_context.templates.render("body_reflection_line")
    star = layout_context.templates.render("body_reflection_star")
    blocks = []
    for prompt in page.metadata.get("prompts", ()):
        blocks.append(
            layout_context.templates.render(
                "body_reflection_prompt",
                label=prompt,
                lines="\n".join([line] * 2),
            )
        )
    stars = "\n".join([star] * int(page.metadata.get("stars", 5)))
    return layout_context.templates.render(
        "body_reflection",
        prompts="\n".join(blocks),
        stars=stars,
    )


@layout("word_search")
def _word_search(layout_context: LayoutContext, page: Page) -> str:
    """The grid is real data, so it is typeset — never drawn by an image model."""
    grid = page.metadata.get("grid", [])
    cells = "\n".join(
        layout_context.templates.render("body_word_search_cell", letter=letter)
        for row in grid
        for letter in row
    )
    words = "\n".join(
        layout_context.templates.render("body_word_search_word", word=word.title())
        for word in page.metadata.get("words", ())
    )
    return layout_context.templates.render(
        "body_word_search",
        columns=page.metadata.get("grid_size", len(grid[0]) if grid else 0),
        rows=len(grid) if grid else page.metadata.get("grid_size", 0),
        cells=cells,
        words=words,
    )


@layout("spot_difference")
def _two_panel(layout_context: LayoutContext, page: Page) -> str:
    panels = []
    for key in ("pdf.panel_top", "pdf.panel_bottom"):
        panels.append(
            layout_context.templates.render(
                "body_two_panel_item",
                label=layout_context.text(key),
                reference=f"prompts/{page.prompt_filename}",
                note=layout_context.text("pdf.art_note"),
            )
        )
    image = layout_context.images.get(page.number)
    if image:
        # A single supplied image already contains both panels.
        return layout_context.templates.render(
            "body_two_panel", panels=layout_context.art(page)
        )
    return layout_context.templates.render("body_two_panel", panels="\n".join(panels))


__all__ = ["LAYOUTS", "LayoutContext", "build_body", "esc", "layout"]
