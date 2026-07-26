"""The local web form: rendering, generation, error handling and file serving."""

from __future__ import annotations

import threading
import urllib.error
import urllib.parse
import urllib.request

import pytest

from src.web import serve

from tests.conftest import DATA_DIR


@pytest.fixture
def site(tmp_path):
    """A running server on an ephemeral port, writing into a temp directory."""
    server = serve("127.0.0.1", 0, output_root=tmp_path / "books", data_dir=DATA_DIR)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def get(path: str):
        with urllib.request.urlopen(base + path) as response:
            return response.status, response.read().decode("utf-8", "replace")

    def post(fields):
        body = urllib.parse.urlencode(fields).encode()
        with urllib.request.urlopen(base + "/generate", data=body) as response:
            return response.status, response.read().decode("utf-8")

    try:
        yield type("Site", (), {"get": staticmethod(get), "post": staticmethod(post),
                                "base": base, "root": tmp_path / "books"})
    finally:
        server.shutdown()
        server.server_close()


def _post_error(site, fields) -> tuple[int, str]:
    try:
        site.post(fields)
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")
    raise AssertionError("expected the form to be rejected")


# -- the form ------------------------------------------------------------


def test_form_renders(site):
    status, body = site.get("/")
    assert status == 200
    assert 'name="destination"' in body
    assert "Travel Activity Book Generator" in body
    assert "$" not in body.split("<style>")[0], "unsubstituted placeholder in the page"


def test_form_offers_the_curated_destinations(site):
    _, body = site.get("/")
    assert "Kfar Hanokdim" in body
    assert body.count('<option value="Kfar Hanokdim">') == 1, "a translated pack is one entry"


def test_form_offers_every_language(site):
    _, body = site.get("/")
    for code in ("en", "he"):
        assert f'value="{code}"' in body


def test_unknown_page_is_a_404(site):
    with pytest.raises(urllib.error.HTTPError) as error:
        site.get("/nope")
    assert error.value.code == 404


# -- generating ----------------------------------------------------------


def test_submitting_the_form_generates_a_book(site):
    status, body = site.post(
        [
            ("destination", "Kfar Hanokdim"),
            ("children", "Noa, Amit"),
            ("ages", "5, 7"),
            ("pages", "10"),
            ("provider", "file"),
            ("interests", "animals"),
            ("html", "1"),
        ]
    )
    assert status == 200
    assert "Your book is ready" in body
    assert "Noa and Amit" in body

    written = site.root / "kfar-hanokdim"
    assert (written / "workbook.json").exists()
    assert (written / "workbook.md").exists()
    assert (written / "workbook.html").exists()
    assert len(list((written / "prompts").glob("*.md"))) == 10


def test_generated_files_are_served(site):
    site.post([("destination", "Prague"), ("provider", "file"), ("pages", "6"), ("html", "1")])
    status, body = site.get("/files/prague/workbook.html")
    assert status == 200
    assert "<html" in body

    status, body = site.get("/files/prague/prompts/01_cover.md")
    assert status == 200
    assert "Portrait A4" in body


def test_hebrew_can_be_requested_from_the_form(site):
    _, body = site.post(
        [
            ("destination", "Kfar Hanokdim"),
            ("children", "נעה"),
            ("ages", "8"),
            ("language", "he"),
            ("pages", "8"),
            ("provider", "file"),
        ]
    )
    assert "כפר הנוקדים" in body


def test_itinerary_is_taken_a_line_at_a_time(site):
    _, body = site.post(
        [
            ("destination", "Kfar Hanokdim"),
            ("provider", "file"),
            ("pages", "8"),
            ("itinerary", "Arrival day\nDesert hike\n\n  Dead Sea  "),
        ]
    )
    assert "Your book is ready" in body
    import json

    data = json.loads((site.root / "kfar-hanokdim" / "workbook.json").read_text(encoding="utf-8"))
    assert data["metadata"]["request"]["trip"]["itinerary"] == [
        "Arrival day", "Desert hike", "Dead Sea"
    ]


def test_free_form_interests_are_merged_with_the_chips(site):
    site.post(
        [
            ("destination", "Prague"),
            ("provider", "file"),
            ("pages", "6"),
            ("interests", "castles"),
            ("interests_other", "boats, volcanoes"),
        ]
    )
    import json

    data = json.loads((site.root / "prague" / "workbook.json").read_text(encoding="utf-8"))
    assert data["metadata"]["request"]["interests"] == ["castles", "boats", "volcanoes"]


def test_the_result_page_flags_pages_that_need_no_illustration(site):
    _, body = site.post(
        [("destination", "Kfar Hanokdim"), ("provider", "file"), ("pages", "14")]
    )
    assert "no illustration needed" in body


def test_an_unknown_destination_is_flagged_as_generic(site):
    _, body = site.post([("destination", "Tbilisi"), ("provider", "file"), ("pages", "6")])
    assert "No data pack for this destination" in body


# -- bad input -----------------------------------------------------------


def test_missing_destination_is_rejected(site):
    status, body = _post_error(site, [("destination", "  "), ("pages", "8")])
    assert status == 400
    assert "destination is required" in body
    assert 'name="destination"' in body, "the form comes back so the user can fix it"


def test_mismatched_ages_are_rejected(site):
    status, body = _post_error(
        site, [("destination", "Prague"), ("children", "Noa"), ("ages", "5, 7")]
    )
    assert status == 400
    assert "one age per child" in body


def test_non_numeric_ages_are_rejected(site):
    status, body = _post_error(
        site, [("destination", "Prague"), ("children", "Noa"), ("ages", "five")]
    )
    assert status == 400
    assert "ages must be whole numbers" in body


def test_submitted_values_survive_an_error(site):
    """A rejected form must not throw away what the user typed."""
    _, body = _post_error(
        site,
        [("destination", "Prague"), ("children", "Noa"), ("ages", "5, 7"),
         ("interests", "castles")],
    )
    assert 'value="Prague"' in body
    assert 'value="Noa"' in body
    assert 'value="castles" checked' in body


def test_input_is_escaped(site):
    """A destination containing markup must not become markup."""
    _, body = _post_error(
        site,
        [("destination", "<script>alert(1)</script>"), ("children", "a"), ("ages", "1,2")],
    )
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


# -- serving is scoped to the output directory ---------------------------


@pytest.mark.parametrize(
    "path",
    ["/files/../../../etc/passwd", "/files/..%2f..%2fetc%2fpasswd", "/files/nope/workbook.json"],
)
def test_files_outside_the_output_directory_are_not_served(site, path):
    with pytest.raises(urllib.error.HTTPError) as error:
        site.get(path)
    assert error.value.code == 404
