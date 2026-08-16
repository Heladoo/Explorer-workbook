"""The lean web form: four fields, photo uploads, and safe file serving."""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.parse
import urllib.request

import pytest

from src.uploads import MAX_FILE_BYTES, UploadError, parse_multipart, safe_stem
from src.web import MAX_PHOTOS, WorkbookFormHandler, serve

from tests.conftest import DATA_DIR

BOUNDARY = "----trip-book-test"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


def _multipart(fields, files=()) -> tuple[bytes, str]:
    """Build a multipart body the way a browser would."""
    parts: list[bytes] = []
    for name, value in fields:
        parts.append(
            f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            + str(value).encode("utf-8")
            + b"\r\n"
        )
    for name, filename, content_type, data in files:
        parts.append(
            f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="{name}"; '
            f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()
            + data
            + b"\r\n"
        )
    parts.append(f"--{BOUNDARY}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={BOUNDARY}"


@pytest.fixture
def site(tmp_path):
    """A running server on an ephemeral port, writing into a temp directory."""
    server = serve("127.0.0.1", 0, output_root=tmp_path / "books", data_dir=DATA_DIR)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"

    def get(path: str):
        with urllib.request.urlopen(base + path) as response:
            return response.status, response.read()

    def submit(fields, files=()):
        body, content_type = _multipart(fields, files)
        request = urllib.request.Request(
            base + "/generate", data=body, headers={"Content-Type": content_type}
        )
        with urllib.request.urlopen(request) as response:
            return response.status, response.read().decode("utf-8")

    try:
        yield type(
            "Site",
            (),
            {
                "get": staticmethod(get),
                "submit": staticmethod(submit),
                "base": base,
                "root": tmp_path / "books",
            },
        )
    finally:
        server.shutdown()
        server.server_close()


def _rejected(site, fields, files=()) -> tuple[int, str]:
    try:
        site.submit(fields, files)
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")
    raise AssertionError("expected the form to be rejected")


def _book(site, slug: str) -> dict:
    return json.loads((site.root / slug / "workbook.json").read_text(encoding="utf-8"))


# -- multipart parsing ----------------------------------------------------


def test_multipart_splits_fields_and_files():
    body, content_type = _multipart(
        [("destination", "Prague"), ("language", "he")],
        [("photos", "kids.png", "image/png", PNG)],
    )
    fields, uploads = parse_multipart(body, content_type)

    assert fields["destination"] == ["Prague"]
    assert fields["language"] == ["he"]
    assert len(uploads) == 1
    assert uploads[0].field == "photos"
    assert uploads[0].data == PNG


def test_empty_file_input_is_not_an_upload():
    """A file input the user left alone still submits an empty part."""
    body, content_type = _multipart(
        [("destination", "Prague")], [("photos", "", "application/octet-stream", b"")]
    )
    _, uploads = parse_multipart(body, content_type)
    assert uploads == []


def test_upload_type_comes_from_content_not_the_name():
    body, content_type = _multipart([], [("photos", "sneaky.png", "image/png", JPEG)])
    _, uploads = parse_multipart(body, content_type)
    assert uploads[0].extension == ".jpg", "the signature wins over the filename"
    assert uploads[0].looks_like_an_image


def test_a_text_file_is_not_an_image():
    body, content_type = _multipart([], [("photos", "notes.txt", "text/plain", b"hello")])
    _, uploads = parse_multipart(body, content_type)
    assert not uploads[0].looks_like_an_image


def test_a_file_over_the_size_limit_is_refused():
    oversized = b"\x00" * (MAX_FILE_BYTES + 1)
    body, content_type = _multipart([], [("photos", "huge.png", "image/png", oversized)])
    with pytest.raises(UploadError, match="huge.png"):
        parse_multipart(body, content_type)


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\me\\photo.JPG", "photo"),
        ("שקד.jpg", "photo-9"),
        ("", "photo-9"),
        ("...", "photo-9"),
    ],
)
def test_filenames_are_made_safe(filename, expected):
    assert safe_stem(filename, "photo-9") == expected


# -- the form -------------------------------------------------------------


def test_form_renders_with_four_fields(site):
    status, raw = site.get("/")
    body = raw.decode("utf-8")
    assert status == 200
    for field in ("destination", "itinerary", "photos", "language"):
        assert f'name="{field}"' in body
    assert "$" not in body.split("<style>")[0], "unsubstituted placeholder in the page"


def test_form_asks_for_nothing_else(site):
    """Lean means lean — no ages, page counts or provider pickers."""
    _, raw = site.get("/")
    body = raw.decode("utf-8")
    for absent in ("name=\"ages\"", "name=\"children\"", "name=\"pages\"", "name=\"seed\""):
        assert absent not in body


def test_form_offers_both_languages(site):
    _, raw = site.get("/")
    body = raw.decode("utf-8")
    assert 'value="en" checked' in body
    assert 'value="he"' in body


def test_unknown_page_is_a_404(site):
    with pytest.raises(urllib.error.HTTPError) as error:
        site.get("/nope")
    assert error.value.code == 404


# -- generating -----------------------------------------------------------


def test_a_destination_alone_is_enough(site):
    """The minimum viable submission."""
    status, body = site.submit([("destination", "Kfar Hanokdim")])
    assert status == 200
    assert "All done" in body

    written = site.root / "kfar-hanokdim"
    assert (written / "workbook.json").exists()
    assert (written / "workbook.md").exists()
    assert (written / "workbook.html").exists()
    illustrated = sum(1 for page in _book(site, "kfar-hanokdim")["pages"] if page["metadata"].get("image_brief"))
    # One prompt file per illustrated page, plus the shared doodle/grid sheet.
    assert len(list((written / "prompts").glob("*.md"))) == illustrated + 1


def test_itinerary_is_taken_a_line_at_a_time(site):
    site.submit(
        [
            ("destination", "Kfar Hanokdim"),
            ("itinerary", "Arrival day\nDesert hike\n\n  Dead Sea  "),
        ]
    )
    trip = _book(site, "kfar-hanokdim")["metadata"]["request"]["trip"]
    assert trip["itinerary"] == ["Arrival day", "Desert hike", "Dead Sea"]


def test_hebrew_can_be_chosen(site):
    _, body = site.submit([("destination", "Kfar Hanokdim"), ("language", "he")])
    assert "כפר הנוקדים" in body


def test_generated_files_are_served(site):
    site.submit([("destination", "Prague")])
    status, raw = site.get("/files/prague/workbook.html")
    assert status == 200
    assert b"<html" in raw

    status, raw = site.get("/files/prague/prompts/01_cover.md")
    assert status == 200
    assert b"Portrait A4" in raw


def test_result_page_flags_pages_that_need_no_picture(site):
    _, body = site.submit([("destination", "Kfar Hanokdim")])
    assert "no picture needed" in body


def test_an_unknown_destination_says_so_kindly(site):
    _, body = site.submit([("destination", "Tbilisi")])
    assert "know this place well yet" in body  # apostrophes arrive escaped


# -- photos ---------------------------------------------------------------


def test_photos_are_saved_beside_the_book(site):
    _, body = site.submit(
        [("destination", "Prague")],
        [
            ("photos", "noa.png", "image/png", PNG),
            ("photos", "amit.jpg", "image/jpeg", JPEG),
        ],
    )
    reference = site.root / "prague" / "reference"
    saved = sorted(path.name for path in reference.iterdir())
    assert saved == ["01-noa.png", "02-amit.jpg"]
    assert (reference / "01-noa.png").read_bytes() == PNG
    assert "made it into the prompts" in body
    assert "Attach all 2" in body


def test_photos_change_every_image_prompt(site):
    """The whole point of uploading them."""
    _, body = site.submit(
        [("destination", "Prague")], [("photos", "noa.png", "image/png", PNG)]
    )
    assert "Attach it when you make the artwork" in body, "singular reads naturally"
    data = _book(site, "prague")
    illustrated = [page for page in data["pages"] if page["metadata"].get("image_brief")]
    assert illustrated
    for page in illustrated:
        assert "reference photograph" in page["image_prompt"]
        assert "01-noa.png" in page["image_prompt"]
        assert "rather than tracing the photo" in page["image_prompt"]


def test_without_photos_the_prompts_describe_generic_children(site):
    site.submit([("destination", "Prague")])
    data = _book(site, "prague")
    joined = " ".join(page["image_prompt"] for page in data["pages"])
    assert "reference photograph" not in joined


def test_photos_are_recorded_in_the_workbook(site):
    site.submit([("destination", "Prague")], [("photos", "noa.png", "image/png", PNG)])
    data = _book(site, "prague")
    assert len(data["metadata"]["family_photos"]) == 1
    assert "reference" in data["metadata"]["family_photos"][0]


def test_the_spec_says_which_photos_to_attach(site):
    site.submit([("destination", "Prague")], [("photos", "noa.png", "image/png", PNG)])
    markdown = (site.root / "prague" / "workbook.md").read_text(encoding="utf-8")
    assert "01-noa.png" in markdown
    assert "Attach them when you generate the artwork" in markdown


def test_a_file_that_is_not_an_image_is_refused(site):
    status, body = _rejected(
        site,
        [("destination", "Prague")],
        [("photos", "notes.txt", "text/plain", b"not a picture")],
    )
    assert status == 400
    assert "look like an image" in body  # apostrophes arrive escaped


def test_too_many_photos_are_refused(site):
    status, body = _rejected(
        site,
        [("destination", "Prague")],
        [("photos", f"kid{index}.png", "image/png", PNG) for index in range(MAX_PHOTOS + 1)],
    )
    assert status == 400
    assert str(MAX_PHOTOS) in body


def test_a_photo_cannot_escape_its_folder(site):
    site.submit(
        [("destination", "Prague")],
        [("photos", "../../../evil.png", "image/png", PNG)],
    )
    saved = list((site.root / "prague" / "reference").iterdir())
    assert len(saved) == 1
    assert saved[0].parent.name == "reference"
    assert not (site.root.parent / "evil.png").exists()


# -- bad input ------------------------------------------------------------


def test_missing_destination_is_rejected(site):
    status, body = _rejected(site, [("destination", "  ")])
    assert status == 400
    assert "we need somewhere to go" in body
    assert 'name="destination"' in body, "the form comes back so it can be fixed"


def test_what_was_typed_survives_an_error(site):
    _, body = _rejected(site, [("destination", ""), ("itinerary", "Day one\nDay two")])
    assert "Day one" in body


def test_input_is_escaped(site):
    _, body = _rejected(
        site, [("destination", ""), ("itinerary", "<script>alert(1)</script>")]
    )
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


def test_a_body_without_a_boundary_is_refused(site):
    request = urllib.request.Request(
        site.base + "/generate",
        data=b"whatever",
        headers={"Content-Type": "multipart/form-data"},
    )
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request)
    assert error.value.code == 400
    assert "boundary" in error.value.read().decode("utf-8")


def test_a_plain_urlencoded_post_still_works(site):
    """Not what the browser sends, but the endpoint should not care."""
    body = urllib.parse.urlencode([("destination", "Prague")]).encode()
    with urllib.request.urlopen(site.base + "/generate", data=body) as response:
        assert response.status == 200


# -- serving is scoped to the output directory ----------------------------


@pytest.mark.parametrize(
    "path",
    ["/files/../../../etc/passwd", "/files/..%2f..%2fetc%2fpasswd", "/files/nope/workbook.json"],
)
def test_files_outside_the_output_directory_are_not_served(site, path):
    with pytest.raises(urllib.error.HTTPError) as error:
        site.get(path)
    assert error.value.code == 404


def test_defaults_are_sane(site):
    """What the form does not ask, it decides well."""
    site.submit([("destination", "Kfar Hanokdim")])
    data = _book(site, "kfar-hanokdim")
    assert data["page_count"] == 12
    assert data["language"] == "en"
    assert data["metadata"]["knowledge_source"] == "file"
    assert WorkbookFormHandler.output_root is not None
