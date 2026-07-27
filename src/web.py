"""A local web form for people who would rather not use the CLI.

    python -m src.web            # then open http://127.0.0.1:8000

Deliberately lean: a destination, an optional itinerary, optional photos of
whoever is coming, and a language. Everything else the generator can decide —
the CLI still exposes the full set.

Ships with local-first product analytics (``src/analytics.py``), a tiny A/B
framework (``src/experiments.py``) and a post-result feedback widget, all off
a first-party visitor cookie — no third-party beacons, no PII, nothing leaves
the machine. See ``/stats`` for the funnel and experiment results.

Standard library only, same as the rest of the project: ``http.server`` plus the
templates in ``src/templates/web/``. It binds to localhost by default — this is
a tool you run on your own machine, not a public service.
"""

from __future__ import annotations

import argparse
import html
import logging
import secrets
import time
import traceback
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, quote, unquote, urlparse

from src.agents.destination_agent import FileKnowledgeProvider
from src.analytics import Analytics, Report, build_analytics
from src.api import generate_workbook
from src.experiments import assignments
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

#: First-party, no third parties involved. A year is plenty for a repeat visit.
VISITOR_COOKIE = "visitor"
VISITOR_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

#: Wording per variant of the "cta" experiment.
CTA_LABELS = {"make_my_book": "Make my book", "build_it": "Build it"}

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
    analytics: Analytics = Analytics()

    # -- routing ---------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - http.server's interface
        path = unquote(urlparse(self.path).path)
        if path == "/":
            visitor, is_new = self._visitor_id()
            variants = assignments(visitor)
            self.analytics.track("form_view", visitor, variants)
            self._send_html(
                self._render_form(visitor=visitor, variants=variants),
                set_visitor=visitor if is_new else None,
            )
        elif path.startswith("/files/"):
            self._send_file(path[len("/files/"):])
        elif path.startswith("/go/"):
            self._redirect_and_track(path[len("/go/"):])
        elif path == "/stats":
            self._send_html(self._render_stats())
        elif path == "/health":
            self._send(200, "application/json", b'{"status":"ok"}')
        else:
            self._send_html(self._render_form(error="That page doesn't exist."), status=404)

    def do_POST(self) -> None:  # noqa: N802 - http.server's interface
        path = unquote(urlparse(self.path).path)
        if path == "/generate":
            self._handle_generate()
        elif path == "/feedback":
            self._handle_feedback()
        else:
            self._send_html(self._render_form(error="Unknown form target."), status=404)

    def log_message(self, format: str, *args: object) -> None:
        logger.info("%s - %s", self.address_string(), format % args)

    # -- visitors and experiments -----------------------------------------

    def _cookie_visitor(self) -> str | None:
        """The visitor id from the request's cookie, if it sent one."""
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        if VISITOR_COOKIE in cookie:
            value = cookie[VISITOR_COOKIE].value.strip()
            return value or None
        return None

    def _visitor_id(self) -> tuple[str, bool]:
        """The caller's id from their cookie, or a fresh one if they have none."""
        existing = self._cookie_visitor()
        if existing:
            return existing, False
        return secrets.token_urlsafe(16), True

    def _form_visitor(self, form: dict[str, list[str]]) -> str:
        """The visitor for a POST: their cookie, falling back to the hidden field.

        The hidden field only matters if cookies are blocked — the cookie set on
        the page they loaded the form from is the source of truth otherwise.
        """
        cookie_visitor = self._cookie_visitor()
        if cookie_visitor:
            return cookie_visitor
        submitted = (form.get("visitor") or [""])[0].strip()
        return submitted or secrets.token_urlsafe(16)

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
        self,
        form: dict[str, list[str]] | None = None,
        error: str | None = None,
        *,
        visitor: str = "",
        variants: dict[str, str] | None = None,
    ) -> str:
        values = form or {}
        variants = variants or {}

        def value(name: str, default: str = "") -> str:
            return _escape((values.get(name) or [default])[0])

        known = FileKnowledgeProvider(self.data_dir).known_destinations()
        chosen_language = (values.get("language") or ["en"])[0]

        optional_template = (
            "optional_fields_tucked.html.tmpl"
            if variants.get("optional_fields") == "tucked"
            else "optional_fields.html.tmpl"
        )
        optional_section = _template(optional_template).substitute(
            itinerary=value("itinerary"), max_photos=MAX_PHOTOS
        )

        return _template("form.html.tmpl").substitute(
            css=_css(),
            message=self._notice("Hmm, that didn't work", error, kind="error") if error else "",
            visitor=_escape(visitor),
            destination=value("destination"),
            optional_section=optional_section,
            cta_label=CTA_LABELS.get(variants.get("cta", ""), "Make my book"),
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

    def _handle_generate(self) -> None:
        try:
            form, uploads = self._read_form()
        except UploadError as exc:
            self._send_html(self._render_form(error=str(exc)), status=400)
            return

        visitor = self._form_visitor(form)
        needs_cookie = self._cookie_visitor() is None
        variants = assignments(visitor)
        self.analytics.track("form_submitted", visitor, variants)
        cookie_to_set = visitor if needs_cookie else None

        try:
            body = self._generate(form, uploads, visitor)
        except (ValueError, RuntimeError) as exc:
            self.analytics.track(
                "generate_failed", visitor, variants, reason=str(exc)[:200]
            )
            self._send_html(
                self._render_form(form=form, error=str(exc), visitor=visitor, variants=variants),
                status=400,
                set_visitor=cookie_to_set,
            )
        except Exception as exc:  # unexpected — show it rather than a blank 500
            logger.error("generation failed: %s", traceback.format_exc())
            self.analytics.track(
                "generate_failed", visitor, variants, reason=f"{type(exc).__name__}"
            )
            self._send_html(
                self._render_form(
                    form=form,
                    error=f"{type(exc).__name__}: {exc}",
                    visitor=visitor,
                    variants=variants,
                ),
                status=500,
                set_visitor=cookie_to_set,
            )
        else:
            self._send_html(body, set_visitor=cookie_to_set)

    def _generate(self, form: dict[str, list[str]], uploads, visitor: str) -> str:
        def one(name: str, default: str = "") -> str:
            return (form.get(name) or [default])[0].strip()

        destination = one("destination")
        if not destination:
            raise ValueError("we need somewhere to go — add a destination")

        language = one("language", "en") or "en"
        itinerary = [line.strip() for line in one("itinerary").splitlines() if line.strip()]
        photos = self._save_photos(uploads, destination)

        started = time.monotonic()
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
        elapsed = round(time.monotonic() - started, 2)

        self.analytics.track(
            "book_created",
            visitor,
            assignments(visitor),
            destination=result.workbook.destination,
            language=result.workbook.language,
            page_count=result.workbook.page_count,
            had_itinerary=bool(itinerary),
            had_photos=bool(photos),
            seconds=elapsed,
        )
        return self._render_result(result, photos, visitor)

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

    def _render_result(self, result, photos: list[Path], visitor: str) -> str:
        workbook = result.workbook
        artifacts = result.artifacts
        context = result.bundle.context
        slug = artifacts.output_dir.name

        def href(path: Path, *, tracked: bool = False) -> str:
            relative = path.relative_to(artifacts.output_dir).as_posix()
            target = f"{quote(slug)}/{quote(relative)}"
            return f"/go/{target}" if tracked else f"/files/{target}"

        def link(path: Path, label: str, note: str) -> str:
            return (
                f'      <a href="{href(path, tracked=True)}">{_escape(label)}'
                f"<small>{_escape(note)}</small></a>"
            )

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
                f'        <li><a href="/go/{quote(slug)}/prompts/{quote(path.name)}">'
                f"{_escape(path.name)}</a></li>"
                for path in artifacts.prompt_files
            ),
            visitor=_escape(visitor),
            book_id=_escape(slug),
        )

    # -- feedback ----------------------------------------------------------

    def _handle_feedback(self) -> None:
        form, _ = self._read_form()

        def one(name: str, default: str = "") -> str:
            return (form.get(name) or [default])[0].strip()

        visitor = one("visitor") or self._form_visitor(form)
        rating = one("rating")
        if rating not in ("great", "fine", "poor"):
            self._send(400, "application/json", b'{"error":"bad rating"}')
            return

        self.analytics.track(
            "feedback",
            visitor,
            rating=rating,
            comment=one("comment")[:2000],
            book=one("book"),
        )
        self._send(200, "application/json", b'{"status":"ok"}')

    # -- redirect-and-track for outbound links ------------------------------

    def _redirect_and_track(self, relative: str) -> None:
        """Log that a produced artifact was opened, then hand off to /files/."""
        visitor, is_new = self._visitor_id()
        self.analytics.track("artifact_opened", visitor, path=relative.split("/", 1)[0])
        self.send_response(302)
        self.send_header("Location", f"/files/{relative}")
        self.send_header("Content-Length", "0")
        if is_new:
            self.send_header(
                "Set-Cookie",
                f"{VISITOR_COOKIE}={visitor}; Max-Age={VISITOR_COOKIE_MAX_AGE}; "
                "Path=/; SameSite=Lax",
            )
        self.end_headers()

    # -- stats ---------------------------------------------------------------

    def _render_stats(self) -> str:
        report = self.analytics.report()
        return _template("stats.html.tmpl").substitute(
            css=_css(),
            window=self._stats_window(report),
            headline=self._stats_headline(report),
            funnel=self._stats_funnel(report),
            experiments=self._stats_experiments(report),
            feedback=self._stats_feedback(report),
            destinations=self._stats_destinations(report),
        )

    def _stats_window(self, report: Report) -> str:
        if not report.events:
            return "No visits recorded yet — open the form once it's live."
        return f"{report.events} events from {report.first_seen} to {report.last_seen}."

    def _stats_headline(self, report: Report) -> str:
        def tile(n: str, label: str) -> str:
            return f'      <div class="stat"><span class="n">{_escape(n)}</span><span class="label">{_escape(label)}</span></div>'

        feedback_score = report.feedback_score
        tiles = [
            tile(str(report.visitors), "Visitors"),
            tile(f"{report.conversion:.0%}", "Made a book"),
            tile(
                f"{report.median_seconds:.1f}s" if report.median_seconds else "—",
                "Median build time",
            ),
            tile(
                f"{feedback_score:.0%}" if feedback_score is not None else "—",
                "Loved it",
            ),
        ]
        return "\n".join(tiles)

    def _stats_funnel(self, report: Report) -> str:
        if not report.funnel or not report.funnel[0].visitors:
            return "      <li>Nothing yet.</li>"
        rows = []
        for step in report.funnel:
            width = round(step.from_top * 100)
            rows.append(
                "      <li><span>"
                f"{_escape(step.label)}</span>"
                f'<span class="bar"><span style="width:{width}%"></span></span>'
                f'<span class="pct">{step.visitors} · {step.from_top:.0%}</span></li>'
            )
        return "\n".join(rows)

    def _stats_experiments(self, report: Report) -> str:
        if not report.experiments:
            return "<p class='hint'>No experiments configured.</p>"
        blocks = []
        for experiment in report.experiments:
            rows = []
            leader = experiment.leader
            for variant in experiment.variants:
                lift = experiment.lift(variant)
                lift_cell = "—"
                if lift is not None:
                    css_class = "lift-up" if lift > 0 else ("lift-down" if lift < 0 else "")
                    lift_cell = f'<span class="{css_class}">{lift:+.0%}</span>'
                is_control = variant.variant == experiment.control
                crown = " 🏆" if leader and variant.variant == leader.variant else ""
                rows.append(
                    "<tr>"
                    f'<td class="{"control" if is_control else ""}">{_escape(variant.variant)}'
                    f'{" (control)" if is_control else ""}{crown}</td>'
                    f"<td>{variant.visitors}</td>"
                    f"<td>{variant.conversions}</td>"
                    f"<td>{variant.rate:.1%}</td>"
                    f"<td>{lift_cell}</td>"
                    "</tr>"
                )
            note = (
                ""
                if experiment.is_decisive
                else '<p class="decisive-note">Still early — under 30 visitors in a '
                "variant, so this could easily flip.</p>"
            )
            blocks.append(
                f"<h3>{_escape(experiment.key)}</h3>"
                f"<p class='hint'>{_escape(experiment.question)}</p>"
                "<table class='variants'><tr><th>Variant</th><th>Visitors</th>"
                "<th>Made a book</th><th>Rate</th><th>vs. control</th></tr>"
                f"{''.join(rows)}</table>{note}"
            )
        return "\n".join(blocks)

    def _stats_feedback(self, report: Report) -> str:
        total = sum(report.feedback.values())
        if not total and not report.comments:
            return "<p class='hint'>No feedback yet.</p>"
        summary = " · ".join(
            f"{label} {report.feedback.get(key, 0)}"
            for key, label in (("great", "🙌"), ("fine", "🙂"), ("poor", "😕"))
        )
        comments = "\n".join(
            f'<div class="comment"><time>{_escape(comment["at"])}</time>'
            f'<span class="rating">{_escape(comment["rating"])}</span>'
            f"{_escape(comment['comment'])}</div>"
            for comment in report.comments
        )
        return f"<p>{summary}</p>\n{comments}"

    def _stats_destinations(self, report: Report) -> str:
        if not report.destinations:
            return "<p class='hint'>Nothing generated yet.</p>"
        return "<p class='hint'>" + " · ".join(
            f"{_escape(name)} ({count})" for name, count in report.destinations
        ) + "</p>"

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

    def _send_html(self, body: str, status: int = 200, *, set_visitor: str | None = None) -> None:
        """``set_visitor`` is the visitor id to persist, when the request had none.

        Must be the same id already used to record events for this request —
        never re-derived here, or the cookie would disagree with what was logged.
        """
        extra_headers = []
        if set_visitor:
            extra_headers.append(
                (
                    "Set-Cookie",
                    f"{VISITOR_COOKIE}={set_visitor}; Max-Age={VISITOR_COOKIE_MAX_AGE}; "
                    "Path=/; SameSite=Lax",
                )
            )
        self._send(status, "text/html; charset=utf-8", body.encode("utf-8"), extra_headers)

    def _send(
        self,
        status: int,
        content_type: str,
        body: bytes,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in extra_headers or []:
            self.send_header(name, value)
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


def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    output_root=None,
    data_dir=None,
    analytics: Analytics | None = None,
):
    """Build the server. Returned rather than started, so tests can drive it."""
    root = Path(output_root or DEFAULT_OUTPUT_ROOT)
    handler = type(
        "ConfiguredHandler",
        (WorkbookFormHandler,),
        {
            "output_root": root,
            "data_dir": Path(data_dir) if data_dir else None,
            "analytics": analytics if analytics is not None else build_analytics(root),
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
    parser.add_argument(
        "--no-analytics",
        action="store_true",
        help="Don't record any events (default: records locally to output/.analytics/).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    root = Path(args.out or DEFAULT_OUTPUT_ROOT)
    analytics = build_analytics(root, enabled=not args.no_analytics)
    server = serve(args.host, args.port, output_root=root, data_dir=args.data_dir, analytics=analytics)
    host = "127.0.0.1" if args.host in ("", "0.0.0.0") else args.host
    print(f"Trip book maker: http://{host}:{server.server_port}")
    if analytics.enabled:
        print(f"Stats: http://{host}:{server.server_port}/stats")
    else:
        print("Analytics disabled (--no-analytics).")
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
