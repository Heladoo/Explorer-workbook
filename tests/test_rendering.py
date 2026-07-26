"""The layout stage: HTML always, PDF when Playwright and Chromium are present."""

from __future__ import annotations

import html as html_module
import re

import pytest

from src import generate_workbook
from src.rendering.html_renderer import HtmlRenderer
from src.rendering.layouts import LAYOUTS
from src.rendering.templates import TemplateSet


@pytest.fixture
def rendered(builder):
    result = generate_workbook(
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[5, 7],
        write=False,
        builder=builder,
    )
    html = HtmlRenderer().render(result.workbook, result.bundle.context)
    return result, html


# -- document structure ------------------------------------------------


def test_every_page_becomes_a_printed_page(rendered):
    result, html = rendered
    for page in result.workbook.pages:
        assert f'id="page-{page.number}"' in html
    # One section per page, plus the contents page.
    assert html.count('<section class="page') == result.workbook.page_count + 1


def test_the_document_is_a4_print_styled(rendered):
    _, html = rendered
    assert "size: A4 portrait" in html
    assert "page-break-after: always" in html
    assert "<style>" in html, "the CSS must be inlined so the file stands alone"


def test_contents_page_lists_every_page(rendered):
    result, html = rendered
    contents = html.split('<section class="page toc"')[1].split("</section>")[0]
    for page in result.workbook.pages:
        assert _esc(page.title) in contents


def test_contents_can_be_switched_off(rendered):
    result, _ = rendered
    html = HtmlRenderer(include_contents=False).render(
        result.workbook, result.bundle.context
    )
    assert "page toc" not in html


def test_instructions_and_titles_reach_the_page(rendered):
    result, html = rendered
    for page in result.workbook.pages:
        assert _esc(page.title) in html
        assert _esc(page.instructions) in html


def test_no_unsubstituted_placeholders(rendered):
    _, html = rendered
    assert not re.search(r"\$\{?[a-z_]+\}?", html), "a template placeholder leaked through"


def test_content_is_html_escaped(builder):
    """A destination or name with markup in it must not break the page."""
    result = generate_workbook(
        destination="Ampersand & <Angle> Bay",
        children=["<script>alert(1)</script>"],
        ages=[6],
        write=False,
        builder=builder,
    )
    html = HtmlRenderer().render(result.workbook, result.bundle.context)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "Ampersand &amp; " in html


# -- placeholders and real artwork ---------------------------------------


def test_pages_without_artwork_show_their_prompt_file(rendered):
    result, html = rendered
    for page in result.workbook.pages:
        assert f"prompts/{page.prompt_filename}" in html
    assert "Illustration goes here" in html


def test_supplied_images_replace_the_placeholder(rendered, tmp_path):
    result, _ = rendered
    artwork = tmp_path / "cover.png"
    artwork.write_bytes(b"\x89PNG\r\n\x1a\n")

    html = HtmlRenderer().render(
        result.workbook, result.bundle.context, images={1: artwork}
    )
    assert artwork.resolve().as_uri() in html
    assert 'class="art filled"' in html
    # Untouched pages keep their placeholder.
    assert "Illustration goes here" in html


# -- per-activity layouts -------------------------------------------------


def test_page_metadata_becomes_real_page_furniture(rendered):
    """The whole point of keeping text out of the illustration."""
    result, html = rendered

    packing = result.workbook.page_by_type("packing")
    for item in packing.metadata["items"]:
        assert _esc(item) in html
    assert html.count('class="checkbox"') >= len(packing.metadata["items"])

    quiz = result.workbook.page_by_type("quiz")
    for question in quiz.metadata["questions"]:
        assert _esc(question["question"]) in html
        for option in question["options"]:
            assert _esc(option) in html
    assert html.count('class="bubble"') == sum(
        len(question["options"]) for question in quiz.metadata["questions"]
    )

    reflection = result.workbook.page_by_type("reflection")
    assert html.count('class="star outline"') >= reflection.metadata["stars"]
    for prompt in reflection.metadata["prompts"]:
        assert _esc(prompt) in html


def test_matching_columns_keep_the_planned_order(rendered):
    result, html = rendered
    matching = result.workbook.page_by_type("matching")
    body = html.split('id="page-%d"' % matching.number)[1].split("</section>")[0]
    left = body.split('class="matching-gutter"')[0]
    right = body.split('class="matching-gutter"')[1]
    for subject in matching.metadata["left_column"]:
        assert _esc(subject) in left
    for subject in matching.metadata["right_column"]:
        assert _esc(subject) in right


def test_spot_the_difference_gets_two_panels(rendered):
    result, html = rendered
    page = result.workbook.page_by_type("spot_difference")
    body = html.split('id="page-%d"' % page.number)[1].split("</section>")[0]
    assert body.count('class="art"') == 2


def test_an_activity_without_a_bespoke_layout_still_prints(rendered):
    """A new activity plugin must not need a layout to be printable."""
    result, html = rendered
    assert "maze" not in LAYOUTS, "maze deliberately uses the default full-page layout"
    maze = result.workbook.page_by_type("maze")
    body = html.split('id="page-%d"' % maze.number)[1].split("</section>")[0]
    assert 'class="art"' in body
    assert _esc(maze.title) in body


def test_page_sections_use_namespaced_classes(rendered):
    """A page class must not collide with an inner layout class.

    ``class="page matching"`` would let the ``.matching`` grid rule style the
    whole sheet, throwing the header and footer into the grid.
    """
    result, html = rendered
    from src.activities.base import ACTIVITY_REGISTRY

    for activity_type in ACTIVITY_REGISTRY:
        assert f'class="page {activity_type}"' not in html
    for page in result.workbook.pages:
        assert f'class="page page-{page.type}"' in html


def test_matching_shadows_are_not_in_the_same_order(rendered):
    """Otherwise every line is drawn straight across and the puzzle is free."""
    result, _ = rendered
    matching = result.workbook.page_by_type("matching")
    left = matching.metadata["left_column"]
    right = matching.metadata["right_column"]
    assert len(left) >= 3
    assert left != right
    assert sorted(left) == sorted(right)


def test_every_registered_layout_names_a_real_activity():
    from src.activities.base import ACTIVITY_REGISTRY

    assert set(LAYOUTS) <= set(ACTIVITY_REGISTRY)


def test_templates_report_a_missing_file_clearly():
    with pytest.raises(FileNotFoundError, match="missing template"):
        TemplateSet().get("body_nonexistent")


# -- writing ---------------------------------------------------------------


def test_html_is_written_alongside_the_other_artifacts(tmp_path, builder):
    result = generate_workbook(
        destination="Prague",
        children=["Noa"],
        ages=[7],
        page_count=6,
        output_dir=tmp_path / "book",
        html=True,
        builder=builder,
    )
    artifacts = result.artifacts
    assert artifacts.workbook_html.exists()
    assert artifacts.workbook_pdf is None
    assert artifacts.workbook_html in artifacts.as_list()
    assert "Prague" in artifacts.workbook_html.read_text(encoding="utf-8")


# -- PDF -------------------------------------------------------------------


def _chromium_available() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    from src.rendering.pdf_renderer import find_chromium

    return find_chromium() is not None


requires_chromium = pytest.mark.skipif(
    not _chromium_available(), reason="Playwright with a Chromium build is not available"
)


@requires_chromium
def test_pdf_is_produced_and_is_a_valid_a4_document(tmp_path, builder):
    result = generate_workbook(
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[5, 7],
        page_count=6,
        output_dir=tmp_path / "book",
        pdf=True,
        builder=builder,
    )
    pdf = result.artifacts.workbook_pdf

    assert pdf.exists()
    raw = pdf.read_bytes()
    assert raw.startswith(b"%PDF-")
    assert raw.rstrip().endswith(b"%%EOF")
    # Contents page plus one page per activity.
    assert raw.count(b"/Type /Page\n") == result.workbook.page_count + 1
    assert result.artifacts.workbook_html.exists(), "--pdf keeps the HTML it printed"


@requires_chromium
def test_pdf_can_be_produced_without_leaving_html_behind(tmp_path, builder):
    from src.rendering.pdf_renderer import PdfRenderer

    result = generate_workbook(
        destination="Prague", page_count=4, write=False, builder=builder
    )
    target = tmp_path / "quiet" / "book.pdf"
    PdfRenderer(keep_html=False).render(
        result.workbook, result.bundle.context, output_path=target
    )
    assert target.exists()
    assert not target.with_suffix(".html").exists()


def _esc(value: str) -> str:
    """Templates escape everything they substitute, so assertions must too."""
    return html_module.escape(value, quote=True)
