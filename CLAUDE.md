# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Generates a printable children's travel activity workbook for any destination —
as data, not as a PDF. Given a destination (and optionally children's names/ages,
an itinerary, interests, and a language), it produces `workbook.json`, a human-readable
`workbook.md`, one image-generation prompt file per page (`prompts/NN_<activity>.md`),
and optionally a print-ready `workbook.html` / `workbook.pdf`. No images are generated —
that stage is an intentional seam (`src/ports.py`).

Python 3.11+, stdlib only for the core generator and web form. The one opt-in
dependency is `playwright` (+ a Chromium build), needed only for `--pdf`.

## Commands

```bash
# Run the full test suite
python -m pytest

# Run one file / one test
python -m pytest tests/test_planner.py
python -m pytest tests/test_puzzles.py::test_every_word_is_findable

# CLI generation
python -m src.cli --destination "Kfar Hanokdim" --children Noa,Amit --ages 5,7 --pages 12
python -m src.cli --destination "Prague" --pdf          # also emits workbook.html/.pdf
python -m src.cli --list-destinations

# Web form
python -m src.web                 # http://127.0.0.1:8000
python -m src.web --no-analytics  # disable the JSONL analytics sink
```

There is no lint/format/type-check tooling configured in this repo — `pytest` is the
only gate. `pytest.ini` sets `testpaths = tests`. `pyproject.toml` exists only as a
dependency manifest (`pdf`/`dev` optional-dependency groups); it declares no lint or
type-check config.

## Architecture

Five agents run in a strict pipeline over one shared, immutable `WorkbookContext`.
No agent or activity ever calls another activity directly — everything flows through
the context and the return values below.

```
CLI / generate_workbook()
        ↓
Agent 1  DestinationKnowledgeAgent  → DestinationKnowledge (landmarks, wildlife, food, weather, …)
        ↓
Agent 2  WorkbookPlanner            → [PlannedPage]  (order, difficulty, target age, focus)
        ↓
Agent 3  ActivityGenerator plugins  → ActivityDraft   (title, instructions, goal, ImageBrief)
        ↓
Agent 4  PromptGenerator            → image_prompt strings + prompts/*.md
        ↓
Agent 5  MarkdownGenerator          → workbook.md          JSON writer → workbook.json
        ↓
Layout   HtmlRenderer → PdfRenderer → workbook.html, workbook.pdf   (optional)
```

The key design decision: activities return a **structured `ImageBrief`**, never a
finished prompt string. `PromptGenerator` (Agent 4) is the *only* component that knows
prompt wording and the global illustration style contract (`src/templates/style_guide.tmpl`),
so the whole book's visual style can change in one place without touching any activity.

| Path | Responsibility |
| --- | --- |
| `src/models/` | `WorkbookContext`, `DestinationKnowledge`, `PlannedPage`, `ImageBrief`, `Page`, `Workbook` |
| `src/agents/` | The five agents (`destination_agent.py`, `planner.py`, `prompt_generator.py`, `markdown_generator.py`) |
| `src/activities/` | One module per activity, auto-discovered — see below |
| `src/locales/` | User-facing copy, one module per language (`en.py`, `he.py`) |
| `src/templates/` | Style guide and markdown templates (`string.Template`, no Jinja) |
| `src/templates/pdf/` | Print page templates and `book.css` |
| `src/rendering/` | Layout stage: workbook → printable HTML (`html_renderer.py`) → PDF (`pdf_renderer.py`) |
| `src/web.py` | Local web form + analytics/A-B/feedback endpoints |
| `src/uploads.py` | From-scratch multipart parser (stdlib `cgi.FieldStorage` is gone in 3.13); file type is sniffed from binary signature, not filename |
| `src/templates/web/` | Form, result page, stats page, and their CSS |
| `src/analytics.py` | JSONL event sink + funnel/conversion/experiment report (`Analytics`, `Report`) |
| `src/experiments.py` | Stateless hash-based A/B assignment (`Experiment`, `ACTIVE`) |
| `src/pipeline.py` | Wires the agents together; every collaborator is constructor-injected |
| `src/output_writer.py` | The only module that touches the filesystem for generated books |
| `src/ports.py` | `ImageBackend` / `DocumentRenderer` Protocols — the seams for real image generation and PDF, unimplemented by design |
| `data/destinations/` | Curated destination knowledge packs (`<slug>.json`, `<slug>.<lang>.json`) |

### Activity plugin contract (`src/activities/base.py`)

Adding an activity is **one new file, no other edits** — `src/activities/__init__.py`
auto-discovers every module in the package via `pkgutil` and each module registers
itself with `@register_activity`. A subclass of `ActivityGenerator` declares
`activity_type`, `min_age`/`max_age`, `energy` ("calm"/"active", used to alternate
pages), `required_knowledge` (categories checked by the default `supports()`), and
implements `generate(context, planned) -> ActivityDraft` using the `self.draft(...)`
and `self.pick(...)` helpers. Files prefixed with `_` (e.g. `_wordbank.py`) are shared
helpers, not activities, and are excluded from auto-discovery.

Two activities (`word_search`, `crossword`) need no illustration at all — the puzzle
grid/answer key is generated in Python and typeset directly by the print layout, so
they're the cheapest pages in the book.

### Knowledge providers (`src/agents/destination_agent.py`)

`--provider` selects a chain, tried in order, with the offline heuristic always
topping up any empty category so activities can rely on their `required_knowledge`:
`file` (curated JSON packs), `llm` (Claude via `urllib`, injectable `transport` so
tests never hit the network, degrades to `file` on any error), `auto` (default: file
first, LLM only if no pack exists), `heuristic` (generic, always succeeds).

### Print layout (`src/rendering/`)

`HtmlRenderer` turns `workbook.json` into print-styled A4 HTML; `PdfRenderer` prints it
with headless Chromium via Playwright. The layout adds no content — it typesets what
activities already recorded in page metadata (checkboxes, quiz options, maze grids,
crossword cells, etc.), which is why activities keep text **out** of illustrations.
A bespoke per-activity-type page layout is a `@layout("your_type")` function in
`src/rendering/layouts.py` plus a template; anything without a registered layout falls
back to a full-page illustration frame automatically.

### Localization (`src/locales/`)

A locale module defines `LANGUAGE`, `STRINGS` (a dict matching `en.py`'s keys),
optional `DIRECTION = "rtl"`, and an optional `TERMS` map. Image prompts are always
rendered in English regardless of workbook language — `PromptGenerator` uses each
destination pack's `illustration_terms` and the locale's `TERMS` to translate a
localized noun back to English before it reaches a prompt. Destination packs support
per-language variants via `<slug>.<language>.json`, falling back to the base
(English) pack for any category the translation omits.

### Web form analytics/A-B/feedback (`src/web.py`, `src/analytics.py`, `src/experiments.py`)

Local-first: events append to a JSONL file (`output_root/.analytics/events.jsonl`),
no third-party beacons, no PII — the only identifier is a random value in a
first-party `visitor` cookie. `AnalyticsSink` is a `Protocol` (mirrors `ImageBackend`/
`DocumentRenderer`), so a real backend later is a new class, not a rewrite.
A/B assignment is stateless: `sha256(f"{experiment_key}:{visitor_id})` picks the
variant deterministically, so nothing needs to be stored to keep a visitor in the
same arm. `/stats` reports the funnel, conversion rate, per-experiment lift, and
feedback tally, computed by `Report.build()` in `src/analytics.py`.

## Notes for making changes

- Never make an activity call another activity or touch the filesystem — everything
  flows through `WorkbookContext` in and `ActivityDraft` out.
- Never hardcode destination-specific strings in a generator; pull from
  `context.knowledge`, which is why the same code works for any destination, with
  or without a curated pack.
- Randomness must go through `context.rng_for(key)` (seeded from a SHA256 hash) so
  a given seed always reproduces byte-identical output — tests rely on this.
- `output/` holds real generated artifacts (including a committed sample run at
  `output/kfar-hanokdim/`) — don't assume it's disposable build output.
