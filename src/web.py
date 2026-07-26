"""A local web form for people who would rather not use the CLI.

    python -m src.web            # then open http://127.0.0.1:8000

Deliberately lean: a destination, an optional itinerary, optional photos of
whoever is coming, and a language. Everything else the generator can decide —
the CLI still exposes the full set.

Standard library only, same as the rest of the project: ``http.server`` plus the
templates in ``src/templates/web/``. It binds to localhost by default — this is
a tool you run on your own machine, not a public service.
"""

from __future__ import annotations

import argparse
import html
import logging
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, quote, unquote, urlparse

from src.agents.destination_agent import FileKnowledgeProvider
from src.api import generate_workbook
from src.models.context import slugify
from src.output_writer import DEFAULT_OUTPUT_ROOT
from src.strings import available_languages
from src.uploads import UploadError, parse_multipart, safe_stem

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "web"

LANGUAGE_NAMES = {"en": "English", "he": "עברית"}

#: Defaults for everything the lean form does not ask about.
DEFAULT_PAGE_COUNT = 12
DEFAULT_PROVIDER = "auto"

MAX_PHOTOS = 6
MAX_BODY_BYTES = 32 * 1024 * 1024
#: Where a book's reference photos live, relative to its output directory.
REFERENCE_DIR = "reference"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".heic": "image/heic",
}


def _template(name: str) -> Template:
    return Template((TEMPLATE_DIR / name).read_text(encoding="utf-8"))


def _css() -> str:
    return (TEMPLATE_DIR / "app.css").read_text(encoding="utf-8")


def _escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


class WorkbookFormHandler(BaseHTTPRequestHandler):
    """Serves the form, runs the generator, and serves what it produced."""

    server_version = "TripBookMaker/1.0"
    output_root: Path = DEFAULT_OUTPUT_ROOT
    data_dir: Path | None = None

    # -- routing ---------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - http.server's interface
        path = unquote(urlparse(self.path).path)
        if path == "/":
            self._send_html(self._render_form())
        elif path.startswith("/files/"):
            self._send_file(path[len("/files/"):])
        elif path == "/health":
            self._send(200, "application/json", b'{"status":"ok"}')
        else:
            self._send_html(self._render_form(error="That page doesn't exist."), status=404)

    def do_POST(self) -> None:  # noqa: N802 - http.server's interface
        if unquote(urlparse(self.path).path) != "/generate":
            self._send_html(self._render_form(error="Unknown form target."), status=404)
            return

        try:
            form, uploads = self._read_form()
        except UploadError as exc:
            self._send_html(self._render_form(error=str(exc)), status=400)
            return

        try:
            self._send_html(self._generate(form, uploads))
        except (ValueError, RuntimeError) as exc:
            self._send_html(self._render_form(form=form, error=str(exc)), status=400)
        except Exception as exc:  # unexpected — show it rather than a blank 500
            logger.error("generation failed: %s", traceback.format_exc())
            self._send_html(
                self._render_form(form=form, error=f"{type(exc).__name__}: {exc}"),
                status=500,
            )

    def log_message(self, format: str, *args: object) -> None:
        logger.info("%s - %s", self.address_string(), format % args)

    # -- reading the form ------------------------------------------------

    def _read_form(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            raise UploadError(
                f"that's more than {MAX_BODY_BYTES // (1024 * 1024)} MB of photos — "
                "try a couple of smaller ones"
            )
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        if content_type.lower().startswith("multipart/form-data"):
            return parse_multipart(body, content_type)
        return parse_qs(body.decode("utf-8"), keep_blank_values=True), []

    def _render_form(
        self, form: dict[str, list[str]] | None = None, error: str | None = None
    ) -> str:
        values = form or {}

        def value(name: str, default: str = "") -> str:
            return _escape((values.get(name) or [default])[0])

        known = FileKnowledgeProvider(self.data_dir).known_destinations()
        chosen_language = (values.get("language") or ["en"])[0]

        return _template("form.html.tmpl").substitute(
            css=_css(),
            message=self._notice("Hmm, that didn't work", error, kind="error") if error else "",
            destination=value("destination"),
            itinerary=value("itinerary"),
            max_photos=MAX_PHOTOS,
            known_options="\n".join(
                f'      <option value="{_escape(name)}"></option>' for name in known
            ),
            language_choices="\n".join(
                '        <label class="chip radio"><input type="radio" name="language" '
                f'value="{_escape(code)}"'
                f'{" checked" if code == chosen_language else ""}>'
                f"<span>{_escape(LANGUAGE_NAMES.get(code, code))}</span></label>"
                for code in available_languages()
            ),
        )

    def _notice(self, heading: str, body: str, *, kind: str = "") -> str:
        return (
            f'  <div class="notice {kind}"><strong>{_escape(heading)}</strong>'
            f"<p>{_escape(body)}</p></div>"
        )

    # -- generation ------------------------------------------------------

    def _generate(self, form: dict[str, list[str]], uploads) -> str:
        def one(name: str, default: str = "") -> str:
            return (form.get(name) or [default])[0].strip()

        destination = one("destination")
        if not destination:
            raise ValueError("we need somewhere to go — add a destination")

        language = one("language", "en") or "en"
        itinerary = [line.strip() for line in one("itinerary").splitlines() if line.strip()]
        photos = self._save_photos(uploads, destination)

        result = generate_workbook(
            destination=destination,
            language=language,
            page_count=DEFAULT_PAGE_COUNT,
            itinerary=itinerary,
            family_photos=[str(path) for path in photos],
            provider=DEFAULT_PROVIDER,
            data_dir=self.data_dir,
            output_root=self.output_root,
            html=True,
            pdf=_pdf_available(),
        )
        return self._render_result(result, photos)

    def _save_photos(self, uploads, destination: str) -> list[Path]:
        """Store reference photos beside the book they belong to."""
        images = [upload for upload in uploads if upload.field == "photos"]
        if not images:
            return []
        if len(images) > MAX_PHOTOS:
            raise ValueError(
                f"that's {len(images)} photos — {MAX_PHOTOS} is plenty for a reference"
            )
        rejected = [upload.filename for upload in images if not upload.looks_like_an_image]
        if rejected:
            raise ValueError(
                f"{rejected[0]} doesn't look like an image — JPEG, PNG, WebP, GIF or HEIC please"
            )

        folder = Path(self.output_root) / slugify(destination) / REFERENCE_DIR
        folder.mkdir(parents=True, exist_ok=True)
        saved = []
        for index, upload in enumerate(images, start=1):
            stem = safe_stem(upload.filename, f"photo-{index}")
            path = folder / f"{index:02d}-{stem}{upload.extension}"
            path.write_bytes(upload.data)
            saved.append(path)
        return saved

    def _render_result(self, result, photos: list[Path]) -> str:
        workbook = result.workbook
        artifacts = result.artifacts
        context = result.bundle.context
        slug = artifacts.output_dir.name

        def href(path: Path) -> str:
            relative = path.relative_to(artifacts.output_dir).as_posix()
            return f"/files/{quote(slug)}/{quote(relative)}"

        def link(path: Path, label: str, note: str) -> str:
            return f'      <a href="{href(path)}">{_escape(label)}<small>{_escape(note)}</small></a>'

        downloads = []
        if artifacts.workbook_pdf:
            downloads.append(link(artifacts.workbook_pdf, "Print it", "A4 PDF"))
        if artifacts.workbook_html:
            downloads.append(link(artifacts.workbook_html, "Have a look", "in your browser"))
        downloads.append(link(artifacts.workbook_json, "workbook.json", "every page as data"))
        downloads.append(link(artifacts.workbook_md, "workbook.md", "the full spec"))

        illustrated = [
            page for page in workbook.pages if page.metadata.get("needs_illustration") is not False
        ]
        free = len(workbook.pages) - len(illustrated)
        summary = (
            f"{len(illustrated)} pages want a picture. Each one has a prompt file below — "
            "paste it into your favourite image tool and drop the result in."
        )
        if free:
            summary += (
                f" The other {free} are already finished: their puzzles are typeset, "
                "so any border art is just decoration."
            )

        reference_note = ""
        if photos:
            thumbs = "\n".join(
                f'        <img src="{href(path)}" alt="reference photo">' for path in photos
            )
            attach = (
                "Attach it when you make the artwork"
                if len(photos) == 1
                else f"Attach all {len(photos)} when you make the artwork"
            )
            reference_note = (
                '    <div class="notice"><strong>Your photos made it into the prompts</strong>'
                "<p>Every prompt now asks for children who look like "
                f"{'this' if len(photos) == 1 else 'these'}. {attach} — most image tools "
                "take a reference picture alongside the prompt.</p>"
                f'<div class="thumbs">\n{thumbs}\n</div></div>'
            )

        notice = ""
        if workbook.metadata.get("language_fallback"):
            notice = self._notice(
                "We don't speak that yet", str(workbook.metadata["language_fallback"])
            )
        elif context and context.knowledge.source == "heuristic":
            notice = self._notice(
                "We don't know this place well yet",
                "The pages use general travel material rather than local facts. Adding a pack "
                "under data/destinations/ fixes that.",
            )

        return _template("result.html.tmpl").substitute(
            css=_css(),
            title=_escape(workbook.title),
            page_count=workbook.page_count,
            message=notice,
            downloads="\n".join(downloads),
            pages="\n".join(
                f'      <li dir="auto">{_escape(page.title)} '
                f'<span class="type">{_escape(page.type)}</span>'
                + (
                    ' <span class="free">no picture needed</span>'
                    if page.metadata.get("needs_illustration") is False
                    else ""
                )
                + "</li>"
                for page in workbook.pages
            ),
            prompt_summary=summary,
            reference_note=reference_note,
            prompt_count=len(artifacts.prompt_files),
            prompt_files="\n".join(
                f'        <li><a href="/files/{quote(slug)}/prompts/{quote(path.name)}">'
                f"{_escape(path.name)}</a></li>"
                for path in artifacts.prompt_files
            ),
        )

    # -- serving generated files ------------------------------------------

    def _send_file(self, relative: str) -> None:
        root = Path(self.output_root).resolve()
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            self._send(404, "text/plain; charset=utf-8", b"not found")
            return
        content_type = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self._send(200, content_type, target.read_bytes())

    # -- plumbing ---------------------------------------------------------

    def _send_html(self, body: str, status: int = 200) -> None:
        self._send(status, "text/html; charset=utf-8", body.encode("utf-8"))

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)


def _pdf_available() -> bool:
    """Only ask for a PDF when a browser is actually there to print it."""
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    from src.rendering.pdf_renderer import find_chromium

    return find_chromium() is not None


def serve(host: str = "127.0.0.1", port: int = 8000, *, output_root=None, data_dir=None):
    """Build the server. Returned rather than started, so tests can drive it."""
    handler = type(
        "ConfiguredHandler",
        (WorkbookFormHandler,),
        {
            "output_root": Path(output_root or DEFAULT_OUTPUT_ROOT),
            "data_dir": Path(data_dir) if data_dir else None,
        },
    )
    return ThreadingHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m src.web",
        description="Serve a local web form for generating travel activity books.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind (default: localhost).")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000).")
    parser.add_argument("--out", default=None, help="Where books are written (default: output/).")
    parser.add_argument("--data-dir", default=None, help="Directory of curated destination packs.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    server = serve(args.host, args.port, output_root=args.out, data_dir=args.data_dir)
    host = "127.0.0.1" if args.host in ("", "0.0.0.0") else args.host
    print(f"Trip book maker: http://{host}:{server.server_port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
