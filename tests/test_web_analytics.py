"""Analytics, A/B assignment and feedback, exercised through the running server."""

from __future__ import annotations

import http.cookiejar
import json
import threading
import urllib.error
import urllib.parse
import urllib.request

import pytest

from src.analytics import Analytics, JsonlSink, NullSink, build_analytics
from src.web import serve

from tests.conftest import DATA_DIR, patch_pdf_unavailable


def _cookie(jar: http.cookiejar.CookieJar, name: str) -> str | None:
    for cookie in jar:
        if cookie.name == name:
            return cookie.value
    return None


@pytest.fixture
def site(tmp_path, monkeypatch):
    """A running server with a real, inspectable analytics sink."""
    patch_pdf_unavailable(monkeypatch)
    analytics = Analytics(JsonlSink(tmp_path / "events.jsonl"))
    server = serve(
        "127.0.0.1", 0, output_root=tmp_path / "books", data_dir=DATA_DIR, analytics=analytics
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def get(path: str):
        with opener.open(base + path) as response:
            return response.status, response.read().decode("utf-8", "replace")

    def submit(fields):
        body = urllib.parse.urlencode(fields).encode()
        request = urllib.request.Request(
            base + "/generate", data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with opener.open(request) as response:
            return response.status, response.read().decode("utf-8")

    def feedback(fields):
        body = urllib.parse.urlencode(fields).encode()
        with opener.open(base + "/feedback", data=body) as response:
            return response.status, response.read().decode("utf-8")

    try:
        yield type(
            "Site",
            (),
            {
                "get": staticmethod(get),
                "submit": staticmethod(submit),
                "feedback": staticmethod(feedback),
                "base": base,
                "jar": jar,
                "analytics": analytics,
            },
        )
    finally:
        server.shutdown()
        server.server_close()


def _events(site):
    return list(site.analytics.sink.replay())


# -- visitor cookie ---------------------------------------------------------


def test_a_fresh_visitor_gets_a_cookie(site):
    site.get("/")
    assert _cookie(site.jar, "visitor") is not None


def test_the_same_visitor_keeps_the_same_cookie_across_requests(site):
    site.get("/")
    first = _cookie(site.jar, "visitor")
    site.get("/")
    assert _cookie(site.jar, "visitor") == first


def test_two_separate_visitors_get_different_ids(site):
    site.get("/")
    a = _cookie(site.jar, "visitor")
    site.jar.clear()
    site.get("/")
    b = _cookie(site.jar, "visitor")
    assert a != b


def test_the_cookie_carries_through_to_generate(site):
    site.get("/")
    cookie_visitor = _cookie(site.jar, "visitor")
    site.submit([("destination", "Prague")])

    events = _events(site)
    visitors = {event.visitor for event in events}
    assert visitors == {cookie_visitor}, "the form view and the submission must agree on who it was"


# -- funnel tracking ----------------------------------------------------


def test_opening_the_form_is_tracked(site):
    site.get("/")
    names = [event.name for event in _events(site)]
    assert names == ["form_view"]


def test_a_full_success_records_the_whole_funnel_up_to_book_created(site):
    site.get("/")
    site.submit([("destination", "Kfar Hanokdim")])

    names = [event.name for event in _events(site)]
    assert names == ["form_view", "form_submitted", "book_created"]


def test_book_created_carries_useful_properties(site):
    site.submit([("destination", "Prague")])
    created = next(event for event in _events(site) if event.name == "book_created")
    assert created.properties["destination"] == "Prague"
    assert created.properties["language"] == "en"
    assert created.properties["page_count"] == 12
    assert isinstance(created.properties["seconds"], float)


def test_a_rejected_submission_records_generate_failed_not_book_created(site):
    with pytest.raises(urllib.error.HTTPError):
        site.submit([("destination", "  ")])
    names = [event.name for event in _events(site)]
    assert "generate_failed" in names
    assert "book_created" not in names
    failure = next(event for event in _events(site) if event.name == "generate_failed")
    assert "somewhere to go" in failure.properties["reason"]


def test_opening_a_produced_file_is_tracked(site):
    """A plain /files/ link is not tracked; the result page must route through /go/."""
    import re

    site.get("/")
    _, result_html = site.submit([("destination", "Kfar Hanokdim")])
    link = re.search(r'href="(/go/[^"]+workbook\.html)"', result_html).group(1)
    site.get(link)

    names = [event.name for event in _events(site)]
    assert "artifact_opened" in names


def test_go_redirects_to_the_real_file(site):
    _, result_html = site.submit([("destination", "Prague")])
    import re

    link = re.search(r'href="(/go/[^"]+workbook\.json)"', result_html).group(1)
    status, body = site.get(link)
    assert status == 200
    assert json.loads(body)["destination"] == "Prague"


# -- variant assignment --------------------------------------------------


def test_the_form_view_event_records_the_visitors_variants(site):
    site.get("/")
    event = _events(site)[0]
    assert set(event.variants) == {"cta", "optional_fields"}
    assert event.variants["cta"] in ("make_my_book", "build_it")


def test_the_same_visitor_sees_the_same_variant_every_time(site):
    site.get("/")
    first = _events(site)[0].variants
    site.get("/")  # same cookie jar, same visitor
    second = _events(site)[1].variants
    assert first == second


def test_the_cta_button_text_matches_the_recorded_variant(site):
    _, body = site.get("/")
    event = _events(site)[0]
    if event.variants["cta"] == "make_my_book":
        assert ">Make my book<" in body
    else:
        assert ">Build it<" in body


def test_the_tucked_variant_hides_the_optional_fields_behind_details(site):
    _, body = site.get("/")
    event = _events(site)[0]
    is_tucked = '<details class="field tucked"' in body
    assert is_tucked == (event.variants["optional_fields"] == "tucked")
    assert 'name="itinerary"' in body, "the field must exist either way"
    assert 'name="photos"' in body


# -- feedback -------------------------------------------------------------


def test_feedback_is_recorded(site):
    site.get("/")
    status, body = site.feedback(
        [("rating", "great"), ("comment", "loved the crossword"), ("book", "prague")]
    )
    assert status == 200
    assert json.loads(body)["status"] == "ok"

    feedback_event = next(event for event in _events(site) if event.name == "feedback")
    assert feedback_event.properties["rating"] == "great"
    assert feedback_event.properties["comment"] == "loved the crossword"


def test_feedback_needs_a_real_rating(site):
    site.get("/")
    with pytest.raises(urllib.error.HTTPError) as error:
        site.feedback([("rating", "amazing"), ("comment", "")])
    assert error.value.code == 400
    assert not [event for event in _events(site) if event.name == "feedback"]


def test_feedback_comment_is_capped(site):
    site.get("/")
    site.feedback([("rating", "poor"), ("comment", "x" * 5000)])
    feedback_event = next(event for event in _events(site) if event.name == "feedback")
    assert len(feedback_event.properties["comment"]) == 2000


# -- stats page -----------------------------------------------------------


def test_stats_page_renders(site):
    site.get("/")
    site.submit([("destination", "Prague")])
    status, body = site.get("/stats")
    assert status == 200
    assert "How the form is doing" in body
    assert "$" not in body.split("<style>")[0]


def test_stats_shows_a_conversion_rate(site):
    site.get("/")
    site.submit([("destination", "Prague")])
    _, body = site.get("/stats")
    assert "Made a book" in body
    assert "100%" in body  # one visitor, one book


def test_stats_lists_the_configured_experiments(site):
    _, body = site.get("/stats")
    assert "cta" in body
    assert "optional_fields" in body


def test_stats_shows_feedback_once_submitted(site):
    site.get("/")
    site.feedback([("rating", "great"), ("comment", "so much fun")])
    _, body = site.get("/stats")
    assert "so much fun" in body


def test_stats_page_with_no_traffic_does_not_crash(tmp_path):
    server = serve("127.0.0.1", 0, output_root=tmp_path, analytics=Analytics(NullSink()))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/stats") as response:
            assert response.status == 200
            assert "No visits recorded yet" in response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()


# -- analytics can be switched off entirely --------------------------------


def test_analytics_disabled_records_nothing(tmp_path):
    analytics = build_analytics(tmp_path, enabled=False)
    server = serve("127.0.0.1", 0, output_root=tmp_path, analytics=analytics)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/") as response:
            assert response.status == 200
        assert not (tmp_path / ".analytics").exists()
    finally:
        server.shutdown()
        server.server_close()
