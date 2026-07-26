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

from dataclasses import dataclass
from typing import Callable

from src.models.context import WorkbookContext
from src.models.page import Page
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

    def art(self, page: Page, *, label: str | None = None, note: str | None = None) -> str:
        """The illustration area: the real image when there is one, else a frame."""
        source = self.images.get(page.number)
        if source:
            return self.templates.render("art_image", src=source, label=page.title)
        return self.templates.render(
            "art",
            label=label or self.strings.text("pdf.illustration"),
            reference=f"prompts/{page.prompt_filename}",
            note=note or self.strings.text("pdf.art_note"),
        )

    def text(self, key: str, **kwargs: str) -> str:
        return self.strings.text(key, **kwargs)


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
    )


@layout("drawing")
def _drawing(layout_context: LayoutContext, page: Page) -> str:
    return layout_context.templates.render(
        "body_default",
        art=layout_context.art(page, label=layout_context.text("pdf.draw_here")),
    )


@layout("packing", "hidden_objects")
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


@layout("quiz")
def _quiz(layout_context: LayoutContext, page: Page) -> str:
    rows = []
    for index, question in enumerate(page.metadata.get("questions", ()), start=1):
        options = "\n".join(
            layout_context.templates.render("body_quiz_option", label=option)
            for option in question.get("options", ())
        )
        rows.append(
            layout_context.templates.render(
                "body_quiz_row",
                number=index,
                question=question.get("question", ""),
                options=options,
            )
        )
    return layout_context.templates.render("body_quiz", rows="\n".join(rows))


@layout("matching")
def _matching(layout_context: LayoutContext, page: Page) -> str:
    def column(values) -> str:
        return "\n".join(
            layout_context.templates.render("body_matching_cell", label=value)
            for value in values
        )

    return layout_context.templates.render(
        "body_matching",
        left=column(page.metadata.get("left_column", ())),
        right=column(page.metadata.get("right_column", ())),
        gutter_note=layout_context.text("pdf.match_gutter"),
    )


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
    blocks = []
    for prompt in page.metadata.get("prompts", ()):
        blocks.append(
            layout_context.templates.render(
                "body_reflection_prompt",
                label=prompt,
                lines='        <div class="ruled"></div>\n' * 2,
            )
        )
    stars = '      <span class="star outline"></span>\n' * int(page.metadata.get("stars", 5))
    return layout_context.templates.render(
        "body_reflection",
        art=layout_context.art(page),
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
        cells=cells,
        words=words,
    )


@layout("crossword")
def _crossword(layout_context: LayoutContext, page: Page) -> str:
    """Print the empty grid with its numbers; the solution stays in metadata."""
    layout_rows = page.metadata.get("layout", [])
    numbers = {
        (entry["row"], entry["column"]): entry["number"]
        for entry in page.metadata.get("numbers", ())
    }
    cells = []
    for row_index, row in enumerate(layout_rows):
        for column_index, square in enumerate(row):
            writable = square == "."
            cells.append(
                layout_context.templates.render(
                    "body_crossword_cell",
                    cell_class="writable" if writable else "blank",
                    number=numbers.get((row_index, column_index), "") if writable else "",
                )
            )

    def clue_list(clues) -> str:
        return "\n".join(
            layout_context.templates.render(
                "body_crossword_clue",
                number=clue["number"],
                clue=clue["clue"],
                length=clue["length"],
            )
            for clue in clues
        )

    columns = page.metadata.get("columns", 0)
    return layout_context.templates.render(
        "body_crossword",
        columns=columns,
        # 13 mm squares where the page allows it, shrinking on a wide grid.
        width=columns * 13,
        cells="\n".join(cells),
        across=clue_list(page.metadata.get("across", ())),
        down=clue_list(page.metadata.get("down", ())),
        across_label=layout_context.text("crossword.across"),
        down_label=layout_context.text("crossword.down"),
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
