"""``read_print_metadata``: which format/count/binding/title an edited

document carries back to the print pipeline — either from its own
data-page-* attributes (documents rendered after those existed), or sniffed
from markup that has been stable for much longer, for every book generated
before then. See src/rendering/print_metadata.py.
"""

from __future__ import annotations

import pytest

from src.rendering.formats import A4_PORTRAIT, A5_BOOKLET
from src.rendering.print_metadata import PrintMetadataError, read_print_metadata


def _doc(*, body: str = "", title: str = "My Book", **html_attrs: str) -> str:
    attrs = " ".join(f'{key}="{value}"' for key, value in html_attrs.items())
    return (
        f"<!DOCTYPE html>\n<html {attrs}><head><title>{title}</title></head>"
        f"<body>{body}</body></html>"
    )


# -- the fast path: explicit data-page-* attributes -----------------------


def test_reads_the_booklet_format_and_slot_count():
    doc = _doc(lang="en", dir="ltr", **{"data-page-format": "a5-booklet", "data-page-count": "12"})
    page_format, page_count, binding, _ = read_print_metadata(doc)
    assert page_format is A5_BOOKLET
    assert page_count == 12
    assert binding == "left"


def test_reads_the_a4_format():
    doc = _doc(**{"data-page-format": "a4-portrait", "data-page-count": "8"})
    page_format, page_count, _, _ = read_print_metadata(doc)
    assert page_format is A4_PORTRAIT
    assert page_count == 8


def test_an_rtl_document_binds_on_the_right():
    doc = _doc(dir="rtl", **{"data-page-format": "a5-booklet", "data-page-count": "12"})
    _, _, binding, _ = read_print_metadata(doc)
    assert binding == "right"


def test_an_ltr_document_binds_on_the_left():
    doc = _doc(dir="ltr", **{"data-page-format": "a5-booklet", "data-page-count": "12"})
    _, _, binding, _ = read_print_metadata(doc)
    assert binding == "left"


def test_reads_the_title():
    doc = _doc(title="The Prague Explorer Workbook", **{"data-page-format": "a5-booklet", "data-page-count": "12"})
    *_, title = read_print_metadata(doc)
    assert title == "The Prague Explorer Workbook"


def test_an_escaped_title_is_unescaped():
    doc = _doc(title="Kids &amp; Family", **{"data-page-format": "a5-booklet", "data-page-count": "12"})
    *_, title = read_print_metadata(doc)
    assert title == "Kids & Family"


def test_a_missing_title_is_an_empty_string():
    doc = '<html data-page-format="a5-booklet" data-page-count="12"><body></body></html>'
    *_, title = read_print_metadata(doc)
    assert title == ""


def test_an_unknown_format_key_is_refused():
    doc = _doc(**{"data-page-format": "a3-poster", "data-page-count": "12"})
    with pytest.raises(PrintMetadataError, match="unknown page format"):
        read_print_metadata(doc)


def test_a_non_numeric_page_count_is_refused():
    doc = _doc(**{"data-page-format": "a5-booklet", "data-page-count": "twelve"})
    with pytest.raises(PrintMetadataError, match="not a number"):
        read_print_metadata(doc)


# -- the fallback: documents rendered before data-page-* existed ----------


def _old_style_doc(*, css_size: str, sections: str, dir: str = "ltr") -> str:
    """A document shaped like anything this project has ever rendered — no
    data-page-* attributes, just the @page rule and .page sections that have
    been part of the markup since before print_metadata.py existed."""
    return (
        f'<!DOCTYPE html>\n<html lang="en" dir="{dir}"><head><title>Old Book</title>'
        f"<style>@page {{ {css_size} }}</style></head><body>{sections}</body></html>"
    )


def test_sniffs_the_a5_booklet_format_with_no_data_attributes():
    doc = _old_style_doc(
        css_size="size: A5 portrait;",
        sections='<section class="page cover" id="page-1"></section>'
        '<section class="page coloring" id="page-2"></section>',
    )
    page_format, page_count, _, _ = read_print_metadata(doc)
    assert page_format is A5_BOOKLET
    assert page_count == 2


def test_sniffs_the_a4_format_with_no_data_attributes():
    doc = _old_style_doc(
        css_size="size: A4 portrait;",
        sections='<section class="page cover" id="page-1"></section>',
    )
    page_format, page_count, _, _ = read_print_metadata(doc)
    assert page_format is A4_PORTRAIT
    assert page_count == 1


def test_sniffed_page_count_counts_a_centre_spread_as_two_slots():
    doc = _old_style_doc(
        css_size="size: A5 portrait;",
        sections=(
            '<section class="page cover" id="page-1"></section>'
            '<section class="page map page-spread" id="page-6"></section>'
            '<section class="page reflection" id="page-8"></section>'
        ),
    )
    _, page_count, _, _ = read_print_metadata(doc)
    assert page_count == 4  # 1 + 2 (the spread) + 1


def test_sniffed_page_count_ignores_the_contents_page():
    doc = _old_style_doc(
        css_size="size: A5 portrait;",
        sections=(
            '<section class="page toc"></section>'
            '<section class="page cover" id="page-1"></section>'
        ),
    )
    _, page_count, _, _ = read_print_metadata(doc)
    assert page_count == 1


def test_no_format_at_all_is_refused():
    doc = "<html><head></head><body><p>not a rendered book</p></body></html>"
    with pytest.raises(PrintMetadataError, match="page format"):
        read_print_metadata(doc)


def test_a_recognised_format_with_no_sections_to_count_is_refused():
    doc = _old_style_doc(css_size="size: A5 portrait;", sections="")
    with pytest.raises(PrintMetadataError, match="page"):
        read_print_metadata(doc)


def test_missing_html_tag_is_refused():
    with pytest.raises(PrintMetadataError, match="no <html> tag"):
        read_print_metadata("<p>not a book</p>")
