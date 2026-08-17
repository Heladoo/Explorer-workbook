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
import json
import logging
import re
import secrets
import tempfile
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
from src.output_writer import DEFAULT_OUTPUT_ROOT, write_additional_format
from src.rendering.formats import A4_PORTRAIT, DEFAULT_PAGE_COUNT, PAGE_COUNT_CHOICES
from src.rendering.print_metadata import PrintMetadataError, read_print_metadata
from src.strings import available_languages, strings_for
from src.templates.web.copy import web_text
from src.uploads import UploadError, parse_multipart, safe_stem

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "web"
STATIC_DIR = TEMPLATE_DIR / "static"

LANGUAGE_NAMES = {"en": "English", "he": "עברית"}

#: Defaults for everything the lean form does not ask about. The page count
#: comes from the shared menu rather than a literal here, so the web form can
#: never offer a length the booklet arithmetic refuses (see
#: src/rendering/formats.py).
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

#: The no-fold A4 alternative to the default A5 booklet, written beside it at
#: generation time — see ``_write_a4_alternative``. Filename by convention
#: rather than a field on ``WrittenArtifacts``: the saved page rediscovers it
#: from a fresh request with no in-memory result to read a path off of.
A4_ALTERNATIVE_FILENAME = "workbook-a4.pdf"

#: The book's own edited copy, saved by ``/print`` after imposition — see
#: ``_handle_print`` and book.html.tmpl's ``printPdf()``.
SAVED_BOOKLET_FILENAME = "workbook-booklet.pdf"

#: The 3-step progress shown identically on the create, review and saved
#: pages (Nielsen's "visibility of system status") — see ``_step_indicator``.
STEP_KEYS = ("step.create", "step.review", "step.save")

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


def _step_indicator(active: int, language: str = "en") -> str:
    """The 1-2-3 progress strip, translated and with ``active`` highlighted.

    Steps before ``active`` render as done, the current one as active, the
    rest as upcoming — the same three states on every one of the three
    pages that includes this, just with a different step lit up.
    """
    items = []
    for index, key in enumerate(STEP_KEYS, start=1):
        state = "done" if index < active else "active" if index == active else ""
        items.append(
            f'    <li class="step {state}"><span class="step-num">{index}</span>'
            f'<span class="step-label">{_escape(web_text(language, key))}</span></li>'
        )
    return '  <ol class="steps">\n' + "\n".join(items) + "\n  </ol>"


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
        elif path.startswith("/static/"):
            self._send_static(path[len("/static/"):])
        elif path.startswith("/files/"):
            self._send_file(path[len("/files/"):])
        elif path.startswith("/go/"):
            self._redirect_and_track(path[len("/go/"):])
        elif path.startswith("/saved/"):
            self._handle_saved(path[len("/saved/"):])
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
        elif path == "/print":
            self._handle_print()
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
        try:
            chosen_page_count = int((values.get("page_count") or [DEFAULT_PAGE_COUNT])[0])
        except ValueError:
            chosen_page_count = DEFAULT_PAGE_COUNT

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
            # Always English, unlike the review/saved pages: the create form's
            # own chrome (labels, hints, CTA) isn't localized at all — the
            # language radio only picks the *workbook's* language — so a
            # translated step indicator here would sit above an otherwise
            # all-English page rather than match it.
            step_indicator=_step_indicator(1),
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
            page_count_choices="\n".join(
                '        <label class="chip radio"><input type="radio" name="page_count" '
                f'value="{count}"'
                f'{" checked" if count == chosen_page_count else ""}>'
                f"<span>{count}</span></label>"
                for count in PAGE_COUNT_CHOICES
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
        page_count = self._chosen_page_count(one("page_count"))
        itinerary = [line.strip() for line in one("itinerary").splitlines() if line.strip()]
        photos = self._save_photos(uploads, destination)

        started = time.monotonic()
        result = generate_workbook(
            destination=destination,
            language=language,
            page_count=page_count,
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
            # A possible English leak isn't shown on the result page (see
            # _render_result) — it's recorded here instead, so a recurring
            # pattern (a destination whose data pack needs translating, an
            # activity that isn't running its text through the locale) shows
            # up as data to triage rather than an in-the-moment scare for
            # whoever is just trying to print a book.
            language_qa_leaks=len(result.language_qa),
        )
        self._write_a4_alternative(result)
        return self._render_result(result, photos)

    def _write_a4_alternative(self, result) -> None:
        """Render the no-fold A4 alternative alongside the default A5 booklet.

        Written eagerly, at the same time as the primary format, rather than
        on demand from the saved page — it comes from the same freshly built
        ``bundle`` already in memory here; reconstructing one from a bare
        ``workbook.json`` later would be a much bigger detour. Skipped
        whenever the primary PDF was (no Chromium, or ``--pdf`` off), and
        never fatal to the book itself if it fails on its own.
        """
        if not (result.artifacts and result.artifacts.workbook_pdf):
            return
        try:
            write_additional_format(
                result.bundle,
                result.artifacts.output_dir,
                A4_PORTRAIT,
                A4_ALTERNATIVE_FILENAME,
            )
        except (RuntimeError, ValueError) as exc:
            logger.warning(
                "no A4 alternative written for %s: %s", result.workbook.destination, exc
            )

    def _chosen_page_count(self, raw: str) -> int:
        """The submitted page count, or the default for anything not on offer.

        Degrades quietly rather than rejecting the submission — a tampered or
        missing value is not something worth stopping someone's book over.
        """
        try:
            count = int(raw)
        except ValueError:
            return DEFAULT_PAGE_COUNT
        return count if count in PAGE_COUNT_CHOICES else DEFAULT_PAGE_COUNT

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
        language = workbook.language
        direction = strings_for(language).direction

        def web(key: str, **kwargs) -> str:
            return web_text(language, key, **kwargs)

        def href(path: Path, *, tracked: bool = False) -> str:
            relative = path.relative_to(artifacts.output_dir).as_posix()
            target = f"{quote(slug)}/{quote(relative)}"
            return f"/go/{target}" if tracked else f"/files/{target}"

        # Only the browser view here — the finished PDFs belong on the saved
        # page (see _render_saved), once there is something actually final to
        # hand over rather than a book that may still be missing pictures.
        downloads = ""
        if artifacts.workbook_html:
            downloads = (
                f'      <a href="{href(artifacts.workbook_html, tracked=True)}" '
                f'target="_blank" rel="noopener">{_escape(web("review.browser_view"))}'
                f'<small>{_escape(web("review.browser_view_note"))}</small></a>'
            )

        illustrated = [
            page for page in workbook.pages if page.metadata.get("needs_illustration") is not False
        ]
        missing = len(illustrated)
        ready = missing == 0
        if ready:
            checklist_body = web("review.checklist_done")
        elif missing == 1:
            checklist_body = web("review.checklist_missing_one")
        else:
            checklist_body = web("review.checklist_missing_many", missing=missing)
        checklist_body += " " + web("review.checklist_invite")

        reference_note = ""
        if photos:
            thumbs = "\n".join(
                f'        <img src="{href(path)}" alt="reference photo">' for path in photos
            )
            attach = web(
                "review.reference_attach_one" if len(photos) == 1 else "review.reference_attach_many",
                count=len(photos),
            )
            body = web("review.reference_body_one" if len(photos) == 1 else "review.reference_body_many")
            reference_note = (
                f'    <div class="notice"><strong>{_escape(web("review.reference_heading"))}</strong>'
                f"<p>{_escape(body)} {_escape(attach)}.</p>"
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
        # Deliberately not shown here: a possible English leak reads as "your
        # book is broken" to a parent who has no way to act on it, and it is
        # very often not a bug at all (an itinerary typed in English inside a
        # Hebrew book legitimately shows those English stop names — see
        # QuizActivity's docstring for the same principle elsewhere). The
        # check still runs on every generation (language_qa above), still
        # gates the test suite (tests/test_localization.py), and is now
        # tracked in the book_created analytics event below instead, so a
        # real pattern shows up in /stats without alarming whoever is just
        # trying to print a book for their kid.

        prompt_items = "\n".join(
            self._prompt_item(index, path, language)
            for index, path in enumerate(artifacts.prompt_files, start=1)
        )

        return _template("result.html.tmpl").substitute(
            css=_css(),
            language=_escape(language),
            direction=direction,
            step_indicator=_step_indicator(2, language),
            eyebrow=_escape(web("review.eyebrow_ready" if ready else "review.eyebrow_almost")),
            title=_escape(workbook.title),
            subtitle=_escape(
                web(
                    "review.subtitle_ready" if ready else "review.subtitle_almost",
                    page_count=workbook.page_count,
                )
            ),
            message=notice,
            downloads=downloads,
            checklist_heading=_escape(web("review.checklist_heading")),
            checklist_body=_escape(checklist_body),
            recommendation=_escape(web("review.recommendation")),
            reference_note=reference_note,
            prompts_heading=_escape(web("review.prompts_heading")),
            prompts_hint=_escape(web("review.prompts_hint")),
            prompt_items=prompt_items,
            make_another=_escape(web("review.make_another")),
        )

    def _prompt_item(self, index: int, path: Path, language: str) -> str:
        """One reveal-to-copy prompt block — see result.html.tmpl's copy button.

        Inlines the prompt text itself rather than linking to the file: the
        point is to use it without ever leaving this page.
        """
        text = path.read_text(encoding="utf-8")
        copy_label = _escape(web_text(language, "review.copy_button"))
        copied_label = _escape(web_text(language, "review.copy_done"))
        return (
            f'      <details class="prompt-item">\n'
            f"        <summary>{_escape(path.name)}</summary>\n"
            f'        <div class="prompt-box">\n'
            f'          <textarea readonly rows="6" id="prompt-{index}">{_escape(text)}</textarea>\n'
            f'          <button type="button" class="copy-btn" data-copied-label="{copied_label}">'
            f"{copy_label}</button>\n"
            f"        </div>\n"
            f"      </details>"
        )

    # -- the saved page (step 3) --------------------------------------------

    def _handle_saved(self, raw_slug: str) -> None:
        slug = raw_slug.strip("/")
        root = Path(self.output_root).resolve()
        book_dir = (root / slug).resolve()
        if not slug or not book_dir.is_relative_to(root) or not (book_dir / "workbook.json").is_file():
            self._send_html(
                self._render_form(error=web_text("en", "saved.not_found")), status=404
            )
            return
        visitor, is_new = self._visitor_id()
        self.analytics.track("saved_view", visitor)
        self._send_html(
            self._render_saved(slug, book_dir, visitor),
            set_visitor=visitor if is_new else None,
        )

    def _render_saved(self, slug: str, book_dir: Path, visitor: str) -> str:
        data = json.loads((book_dir / "workbook.json").read_text(encoding="utf-8"))
        language = str(data.get("language") or "en")
        title = str(data.get("title") or "")
        page_count = int(data.get("page_count") or 0)
        direction = strings_for(language).direction

        def web(key: str, **kwargs) -> str:
            return web_text(language, key, **kwargs)

        def go(name: str) -> str:
            return f"/go/{quote(slug)}/{quote(name)}"

        def link(name: str, label_key: str, note_key: str, **note_kwargs) -> str:
            return (
                f'      <a href="{go(name)}" target="_blank" rel="noopener">'
                f"{_escape(web(label_key))}<small>{_escape(web(note_key, **note_kwargs))}</small></a>"
            )

        downloads = []
        if (book_dir / SAVED_BOOKLET_FILENAME).is_file():
            downloads.append(
                link(
                    SAVED_BOOKLET_FILENAME,
                    "saved.booklet_label",
                    "saved.booklet_note",
                    sheets=max(page_count // 4, 1),
                )
            )
        if (book_dir / A4_ALTERNATIVE_FILENAME).is_file():
            downloads.append(link(A4_ALTERNATIVE_FILENAME, "saved.a4_label", "saved.a4_note"))
        has_editor = (book_dir / "workbook.html").is_file()
        if has_editor:
            downloads.append(link("workbook.html", "saved.browser_label", "saved.browser_note"))

        # "Back" returns to the previous step — the browser editor is what
        # that step actually is once a book has been saved (see the redesign
        # notes: step 2's own review page is generated fresh per POST, so
        # there's nothing static to return *to* there). Omitted rather than
        # dead-linked when the editor was never written (no PDF backend).
        back_href = go("workbook.html") if has_editor else ""

        return _template("saved.html.tmpl").substitute(
            css=_css(),
            language=_escape(language),
            direction=direction,
            step_indicator=_step_indicator(3, language),
            eyebrow=_escape(web("saved.eyebrow")),
            title=_escape(title),
            subtitle=_escape(web("saved.subtitle")),
            downloads="\n".join(downloads),
            back_action=(
                f'<a class="button secondary" href="{back_href}" target="_blank" '
                f'rel="noopener">{_escape(web("saved.back_label"))}</a>'
                if back_href
                else ""
            ),
            start_over_label=_escape(web("saved.start_over_label")),
            share_label=_escape(web("saved.share_label")),
            share_copied=_escape(web("saved.share_copied")),
            feedback_heading=_escape(web("saved.feedback_heading")),
            feedback_great=_escape(web("saved.feedback_great")),
            feedback_fine=_escape(web("saved.feedback_fine")),
            feedback_poor=_escape(web("saved.feedback_poor")),
            feedback_placeholder=_escape(web("saved.feedback_placeholder")),
            feedback_send=_escape(web("saved.feedback_send")),
            feedback_thanks=_escape(web("saved.feedback_thanks")),
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

    # -- printing an edited document ----------------------------------------

    def _handle_print(self) -> None:
        """Print a (possibly hand-edited) workbook document straight to PDF.

        The in-browser editor's "Save as PDF" button posts its edited
        document here instead of calling ``window.print()`` — a browser's own
        print dialog only ever offers loose page sizes (A4, Letter, ...), with
        no way to ask it for this book's real format (A5, two-up on an A4
        sheet, folded and stapled). This runs the exact same headless-Chromium
        + imposition pipeline ``--pdf`` uses, keyed off what the document
        itself says about how to print it (see
        ``src/rendering/print_metadata.py``) — so the result matches the
        book's actual format, edited or not, even for a book saved before
        this endpoint existed.

        A ``?slug=`` query parameter names which book on this server the
        posted document belongs to — set by book.html.tmpl whenever it was
        opened through ``/files/<slug>/...`` rather than off local disk. When
        it resolves to a real output directory, the edited document and its
        freshly imposed PDF are written back there (see ``_persist_saved_book``)
        and the response carries an ``X-Saved-Slug`` header, which is what
        tells the editor's JS to hand the browser off to the saved page
        (``/saved/<slug>``) instead of just downloading the PDF.
        """
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send(400, "text/plain; charset=utf-8", b"missing or oversized document")
            return
        html_text = self.rfile.read(length).decode("utf-8", errors="replace")

        try:
            page_format, page_count, binding, title = read_print_metadata(html_text)
        except PrintMetadataError as exc:
            self._send(400, "text/plain; charset=utf-8", str(exc).encode("utf-8"))
            return

        if not _pdf_available():
            self._send(
                503,
                "text/plain; charset=utf-8",
                b"PDF rendering isn't set up on this server (Playwright/Chromium missing).",
            )
            return

        from src.rendering.pdf_renderer import PdfRenderer

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            try:
                pdf_path = PdfRenderer(keep_html=False).render_html(
                    html_text, tmp_dir / "workbook.pdf"
                )
            except RuntimeError as exc:
                self._send(500, "text/plain; charset=utf-8", str(exc).encode("utf-8"))
                return

            # Fold-and-staple sheets, the same "second file, never instead"
            # rule output_writer._impose follows — a failure here (unfoldable
            # length, missing pypdf) costs only the imposed copy, not the
            # readable one already on disk. Unlike output_writer, there is no
            # second call site quietly reading workbook_booklet_pdf here — the
            # editor's button downloads whatever comes back, so a silent
            # fallback would hand someone plain A5 pages with no sign anything
            # was ever meant to fold. booklet_warning carries the reason back
            # as a response header instead, for the button to surface.
            booklet_warning: str | None = None
            if page_format.booklet:
                if page_count % 4:
                    booklet_warning = (
                        f"{page_count} pages is not a multiple of 4, so this book can't "
                        "be folded into a booklet — these are plain A5 pages instead."
                    )
                else:
                    try:
                        from src.rendering.imposition import impose_booklet

                        pdf_path = impose_booklet(
                            pdf_path,
                            tmp_dir / "workbook-booklet.pdf",
                            page_format=page_format,
                            page_count=page_count,
                            binding=binding,
                        )
                    except (RuntimeError, ValueError) as exc:
                        booklet_warning = str(exc)
                        debug_path = self._save_print_debug_copy(html_text)
                        logger.warning(
                            "printing %d pages without booklet imposition: %s "
                            "(posted document saved to %s for inspection)",
                            page_count,
                            exc,
                            debug_path,
                        )

            data = pdf_path.read_bytes()

        headers = [("Content-Disposition", _content_disposition(title))]
        if booklet_warning:
            headers.append(("X-Print-Warning", quote(booklet_warning)))
        slug = self._resolve_book_slug()
        if slug:
            imposed = page_format.booklet and not booklet_warning
            self._persist_saved_book(slug, html_text, data, imposed=imposed)
            headers.append(("X-Saved-Slug", quote(slug)))
        self._send(200, "application/pdf", data, headers)

    def _resolve_book_slug(self) -> str | None:
        """The ``?slug=`` query param, only if it names a real output directory.

        A stale or tampered slug (a book deleted since the tab was opened, or
        anything trying path traversal) degrades to "not saved anywhere" —
        the PDF still downloads either way, it just doesn't redirect.
        """
        query = parse_qs(urlparse(self.path).query)
        slug = (query.get("slug") or [""])[0].strip()
        if not slug:
            return None
        root = Path(self.output_root).resolve()
        book_dir = (root / slug).resolve()
        if not book_dir.is_relative_to(root) or not book_dir.is_dir():
            return None
        return slug

    def _persist_saved_book(
        self, slug: str, html_text: str, pdf_data: bytes, *, imposed: bool
    ) -> None:
        """Write the just-printed edit back into the book's own output folder.

        Never fatal — a disk hiccup here should not cost the download the
        request actually came for. ``imposed`` picks the filename: a real
        fold-and-staple booklet is kept apart from the plain-pages fallback
        (see ``_handle_print``'s ``booklet_warning``) so the saved page never
        calls an unfoldable PDF a booklet.
        """
        try:
            book_dir = Path(self.output_root) / slug
            (book_dir / "workbook.html").write_text(html_text, encoding="utf-8")
            filename = SAVED_BOOKLET_FILENAME if imposed else "workbook.pdf"
            (book_dir / filename).write_bytes(pdf_data)
        except OSError as exc:
            logger.warning("could not persist saved edits for %s: %s", slug, exc)

    def _save_print_debug_copy(self, html_text: str) -> Path:
        """Keep the exact posted document when imposition fails on it.

        A failure here has been hard to pin down from the PDF alone — the
        rendered page count disagreeing with the declared one could come from
        several different DOM shapes a real browser's edit-then-serialize
        round trip might produce, and none reproduced yet from a synthetic
        POST. Keeping the actual bytes turns the next occurrence into
        something inspectable instead of another guess.
        """
        debug_dir = Path(self.output_root) / ".print-debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        path = debug_dir / f"{int(time.time())}.html"
        path.write_text(html_text, encoding="utf-8")
        return path

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
            qa_leaks=self._stats_qa_leaks(report),
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

    def _stats_qa_leaks(self, report: Report) -> str:
        """Backlog view of possible English leaks — see src/qa.py and
        _render_result's notice comment: this is where a leak goes instead
        of the result page, so it needs somewhere a developer actually looks."""
        if not report.qa_leaks:
            return "<p class='hint'>None recorded.</p>"
        return "<p class='hint'>" + " · ".join(
            f"{_escape(name)} ({count})" for name, count in report.qa_leaks
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

    def _send_static(self, relative: str) -> None:
        """Serve a fixed asset shipped with the templates, e.g. the logo."""
        root = STATIC_DIR.resolve()
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


def _content_disposition(title: str) -> str:
    """Name a /print download after the book itself, not the generic
    "workbook.pdf" every download used to share.

    A title is very often not ASCII (Hebrew, Greek, ...), so this carries it
    twice: ``filename*`` (RFC 6266) is the real title, percent-encoded UTF-8,
    which every current browser reads; the plain ``filename`` stays an ASCII
    fallback for anything older that only understands that form.
    """
    base = re.sub(r'[\\/:*?"<>|\r\n]+', " ", title or "").strip()
    base = re.sub(r"\s+", " ", base) or "workbook"
    ascii_fallback = base.encode("ascii", "ignore").decode("ascii").strip() or "workbook"
    return (
        f'attachment; filename="{ascii_fallback}.pdf"; '
        f"filename*=UTF-8''{quote(f'{base}.pdf')}"
    )


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
