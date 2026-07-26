"""A local web form for people who would rather not use the CLI.

    python -m src.web            # then open http://127.0.0.1:8000

Standard library only, same as the rest of the project: ``http.server`` plus the
templates in ``src/templates/web/``. It binds to localhost by default — this is
a tool you run on your own machine, not a public service.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, quote, unquote, urlparse

from src.agents.destination_agent import FileKnowledgeProvider
from src.api import generate_workbook
from src.output_writer import DEFAULT_OUTPUT_ROOT
from src.strings import available_languages, strings_for

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "web"

#: Offered as one-click chips; anything else goes in the free-text field.
SUGGESTED_INTERESTS = (
    "animals", "castles", "trains", "science", "dinosaurs", "food", "art", "nature",
)

LANGUAGE_NAMES = {"en": "English", "he": "עברית (Hebrew)"}

PROVIDERS = (
    ("auto", "Curated pack, then the model"),
    ("file", "Curated packs only (offline)"),
    ("llm", "Ask Claude first"),
    ("heuristic", "Generic material only"),
)

DIFFICULTIES = (
    ("", "Ramp up through the book"),
    ("easy", "Easy throughout"),
    ("medium", "Medium throughout"),
    ("hard", "Hard throughout"),
)

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
}


def _template(name: str) -> Template:
    return Template((TEMPLATE_DIR / name).read_text(encoding="utf-8"))


def _css() -> str:
    return (TEMPLATE_DIR / "app.css").read_text(encoding="utf-8")


def _escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


class WorkbookFormHandler(BaseHTTPRequestHandler):
    """Serves the form, runs the generator, and serves what it produced."""

    server_version = "TravelWorkbook/1.0"
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
            self._send_html(self._render_form(error="That page does not exist."), status=404)

    def do_POST(self) -> None:  # noqa: N802 - http.server's interface
        if unquote(urlparse(self.path).path) != "/generate":
            self._send_html(self._render_form(error="Unknown form target."), status=404)
            return

        form = self._read_form()
        try:
            self._send_html(self._generate(form))
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

    # -- form ------------------------------------------------------------

    def _read_form(self) -> dict[str, list[str]]:
        length = int(self.headers.get("Content-Length") or 0)
        if length > 1_000_000:
            raise ValueError("that form is far too large")
        body = self.rfile.read(length).decode("utf-8")
        return parse_qs(body, keep_blank_values=True)

    def _render_form(
        self, form: dict[str, list[str]] | None = None, error: str | None = None
    ) -> str:
        values = form or {}

        def value(name: str, default: str = "") -> str:
            return _escape((values.get(name) or [default])[0])

        chosen_interests = set(values.get("interests", []))
        known = FileKnowledgeProvider(self.data_dir).known_destinations()

        return _template("form.html.tmpl").substitute(
            css=_css(),
            message=self._notice("Could not build that book", error, kind="error")
            if error
            else "",
            destination=value("destination"),
            children=value("children"),
            ages=value("ages"),
            interests_other=value("interests_other"),
            itinerary=value("itinerary"),
            duration_days=value("duration_days"),
            start_date=value("start_date"),
            pages=value("pages", "12"),
            seed=value("seed", "0"),
            known_names=_escape(", ".join(known)) or "none yet",
            known_options="\n".join(
                f'        <option value="{_escape(name)}"></option>' for name in known
            ),
            interest_chips="\n".join(
                '        <label class="chip"><input type="checkbox" name="interests" '
                f'value="{_escape(interest)}"'
                f'{" checked" if interest in chosen_interests else ""}>'
                f"<span>{_escape(interest)}</span></label>"
                for interest in SUGGESTED_INTERESTS
            ),
            language_options=self._options(
                [(code, LANGUAGE_NAMES.get(code, code)) for code in available_languages()],
                value("language", "en"),
            ),
            difficulty_options=self._options(DIFFICULTIES, value("difficulty")),
            provider_options=self._options(PROVIDERS, value("provider", "auto")),
            html_checked="checked" if not form or values.get("html") else "",
            pdf_checked="checked" if values.get("pdf") else "",
        )

    def _options(self, choices, selected: str) -> str:
        return "\n".join(
            f'            <option value="{_escape(code)}"'
            f'{" selected" if code == selected else ""}>{_escape(label)}</option>'
            for code, label in choices
        )

    def _notice(self, heading: str, body: str, *, kind: str = "") -> str:
        return (
            f'  <div class="notice {kind}"><strong>{_escape(heading)}</strong>'
            f"<p>{_escape(body)}</p></div>"
        )

    # -- generation ------------------------------------------------------

    def _generate(self, form: dict[str, list[str]]) -> str:
        def one(name: str, default: str = "") -> str:
            return (form.get(name) or [default])[0].strip()

        def number(name: str, default: int | None) -> int | None:
            raw = one(name)
            if not raw:
                return default
            try:
                return int(raw)
            except ValueError as exc:
                raise ValueError(f"{name.replace('_', ' ')} must be a whole number") from exc

        children = _split(one("children"))
        ages_raw = _split(one("ages"))
        try:
            ages = [int(age) for age in ages_raw]
        except ValueError as exc:
            raise ValueError("ages must be whole numbers, separated by commas") from exc
        if ages and len(ages) != len(children):
            raise ValueError(
                f"got {len(ages)} age(s) for {len(children)} name(s) — "
                "give one age per child, in the same order"
            )

        interests = [*form.get("interests", []), *_split(one("interests_other"))]
        itinerary = [line.strip() for line in one("itinerary").splitlines() if line.strip()]
        wants_pdf = bool(form.get("pdf"))
        wants_html = bool(form.get("html")) or wants_pdf

        result = generate_workbook(
            destination=one("destination"),
            children=children,
            ages=ages,
            language=one("language", "en") or "en",
            page_count=number("pages", 12) or 12,
            difficulty=one("difficulty") or None,
            interests=interests,
            itinerary=itinerary,
            duration_days=number("duration_days", None),
            start_date=one("start_date") or None,
            seed=number("seed", 0) or 0,
            provider=one("provider", "auto") or "auto",
            data_dir=self.data_dir,
            output_root=self.output_root,
            html=wants_html,
            pdf=wants_pdf,
        )
        return self._render_result(result)

    def _render_result(self, result) -> str:
        workbook = result.workbook
        artifacts = result.artifacts
        context = result.bundle.context
        slug = artifacts.output_dir.name
        strings = strings_for(workbook.language)

        def link(path: Path, label: str, note: str) -> str:
            href = f"/files/{quote(slug)}/{quote(path.relative_to(artifacts.output_dir).as_posix())}"
            return f'      <a href="{href}">{_escape(label)}<small>{_escape(note)}</small></a>'

        downloads = []
        if artifacts.workbook_html:
            downloads.append(link(artifacts.workbook_html, "Printable pages", "HTML, ready to print"))
        if artifacts.workbook_pdf:
            downloads.append(link(artifacts.workbook_pdf, "PDF", "A4, one page per activity"))
        downloads.append(link(artifacts.workbook_json, "workbook.json", "the full structure"))
        downloads.append(link(artifacts.workbook_md, "workbook.md", "the build specification"))

        illustrated = [
            page for page in workbook.pages if page.metadata.get("needs_illustration") is not False
        ]
        free = len(workbook.pages) - len(illustrated)
        prompt_summary = (
            f"{len(illustrated)} pages need an illustration — generate each from its prompt "
            f"file and drop it in."
        )
        if free:
            prompt_summary += (
                f" {free} page(s) are complete already: their puzzle is typeset, "
                "so any border art is optional."
            )

        notice = ""
        if workbook.metadata.get("language_fallback"):
            notice = self._notice(
                "Language not available", str(workbook.metadata["language_fallback"])
            )
        elif context and context.knowledge.source == "heuristic":
            notice = self._notice(
                "No data pack for this destination",
                "The pages use generic travel material. Add a pack under data/destinations/, "
                "or choose 'Ask Claude first' to fetch real facts.",
            )

        return _template("result.html.tmpl").substitute(
            css=_css(),
            title=_escape(workbook.title),
            destination=_escape(workbook.destination),
            children_phrase=_escape(
                f", for {strings.join(context.child_names)}"
                if context and context.child_names
                else ""
            ),
            page_count=workbook.page_count,
            message=notice,
            downloads="\n".join(downloads),
            pages="\n".join(
                f'      <li dir="auto">{_escape(page.title)} '
                f'<span class="type">{_escape(page.type)}</span>'
                + (
                    ' <span class="free">no illustration needed</span>'
                    if page.metadata.get("needs_illustration") is False
                    else ""
                )
                + "</li>"
                for page in workbook.pages
            ),
            prompt_summary=prompt_summary,
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


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


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
    print(f"Travel activity book generator: http://{host}:{server.server_port}")
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
