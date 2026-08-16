"""Agent 4 owns the style contract that every prompt must satisfy."""

from __future__ import annotations

import pytest

from src.activities.base import available_activities
from src.agents.prompt_generator import PromptGenerator, StyleGuide
from src.models.page import ImageBrief, RenderMode
from src.models.plan import PlannedPage

#: Requirements from the brief that must hold for every single prompt.
REQUIRED_PHRASES = (
    "Portrait A4",
    "No text",
    "Prints cleanly in black and white",
    "children's travel activity book",
)


@pytest.fixture
def generator() -> PromptGenerator:
    return PromptGenerator()


def _all_prompts(context, generator) -> list[tuple[str, str]]:
    """One rendered prompt per activity that actually asks for an illustration.

    Most activities carry no ``image_brief`` at all now — only cover and
    coloring pages do (see ``src/pipeline.py``) — so activities with nothing
    to render are skipped rather than exercised here.
    """
    prompts = []
    for activity in available_activities():
        planned = PlannedPage(
            number=2, activity_type=activity.activity_type, difficulty="medium", focus="wildlife"
        )
        draft = activity.generate(context, planned)
        if draft.image_brief is None:
            continue
        prompts.append((activity.activity_type, generator.render(draft.image_brief, context)))
    return prompts


def test_every_prompt_carries_the_style_contract(context, generator):
    for activity_type, prompt in _all_prompts(context, generator):
        for phrase in REQUIRED_PHRASES:
            assert phrase in prompt, f"{activity_type} prompt is missing {phrase!r}"


def test_every_prompt_is_destination_aware(context, generator):
    for activity_type, prompt in _all_prompts(context, generator):
        known = [
            value
            for name in ("landmarks", "wildlife", "plants", "activities", "local_food")
            for value in context.knowledge.get(name)
        ]
        assert context.destination in prompt or any(value in prompt for value in known), (
            f"{activity_type} prompt mentions nothing specific to the destination"
        )


def test_every_prompt_shares_one_visual_style(context, generator):
    signatures = {
        prompt.split("Visually consistent with every other page of this book:")[1].split("\n")[0]
        for _, prompt in _all_prompts(context, generator)
    }
    assert len(signatures) == 1, "pages must declare the same style signature"


def test_recurring_characters_are_described_consistently(context, generator):
    for _, prompt in _all_prompts(context, generator):
        assert "Recurring characters" in prompt
        assert "about 5 and about 7 years old" in prompt


def test_no_characters_block_without_children(context, generator):
    from dataclasses import replace

    solo = replace(context, children=())
    prompt = generator.render(ImageBrief(subject="a lighthouse"), solo)
    assert "Recurring characters" not in prompt


def test_coloring_pages_forbid_shading(generator, context):
    prompt = generator.render(
        ImageBrief(subject="a lighthouse", render_mode=RenderMode.COLORING), context
    )
    assert "no shading" in prompt
    assert "coloring page" in prompt


def test_fact_pages_allow_light_shading(generator, context):
    prompt = generator.render(
        ImageBrief(subject="a puffin", render_mode=RenderMode.ILLUSTRATION), context
    )
    assert "light grey shading" in prompt


def test_sections_appear_in_a_predictable_order(generator, context):
    prompt = generator.render(
        ImageBrief(
            subject="a lighthouse",
            scene="A lighthouse on a cliff.",
            elements=("puffins", "waves"),
            composition="One full-page scene.",
            extra_constraints=("Keep the beam simple.",),
        ),
        context,
    )
    positions = [prompt.index(header) for header in ("Scene:", "Include:", "Layout:", "Style:", "Constraints:")]
    assert positions == sorted(positions)
    assert "• puffins" in prompt
    assert "• Keep the beam simple." in prompt


def test_optional_sections_are_omitted_when_empty(generator, context):
    prompt = generator.render(ImageBrief(subject="a lighthouse"), context)
    assert "Include:" not in prompt
    assert "Layout:" not in prompt


def test_age_band_reaches_the_prompt(generator, context):
    prompt = generator.render(ImageBrief(subject="a lighthouse"), context)
    assert "Age-appropriate for a 5-7 year old" in prompt


def test_prompt_override_is_used_verbatim(generator, context):
    brief = ImageBrief(subject="anything", prompt_override="Draw a single red circle.")
    assert generator.render(brief, context) == "Draw a single red circle.\n"


def test_a_different_style_guide_changes_every_prompt(generator, context):
    house_style = PromptGenerator(StyleGuide(signature="woodcut prints throughout"))
    brief = ImageBrief(subject="a lighthouse")
    assert "woodcut prints throughout" in house_style.render(brief, context)
    assert "woodcut" not in generator.render(brief, context)


def test_doodle_grid_lists_every_subject(generator, context):
    prompt = generator.render_doodle_grid(["a camel", "a fig tree", "a market stall"], context)
    for subject in ("a camel", "a fig tree", "a market stall"):
        assert f"• {subject}" in prompt
    assert "coloring page" in prompt
    assert "cropped into its own individual symbol drawing" in prompt
    assert "No grid lines" in prompt


def test_doodle_grid_names_the_destination(generator, context):
    prompt = generator.render_doodle_grid(["a camel"], context)
    assert context.destination in prompt


def test_prompt_file_contains_only_the_prompt(generator, context):
    prompt = generator.render(ImageBrief(subject="a lighthouse"), context)
    body = generator.prompt_file(prompt)
    assert body == prompt
    assert not body.startswith("#"), "prompt files carry no markdown headings"
    assert body.endswith("\n")
