# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Generates a printable children's travel activity workbook for any destination —
as data first, images second. Given a destination (and optionally children's
names/ages, an itinerary, interests, and a language), it produces `workbook.json`,
a human-readable `workbook.md`, one image-generation prompt file per page
(`prompts/NN_<activity>.md`), per-symbol prompts (`prompts/symbols/<slug>.md`),
and optionally a print-ready `workbook.html` / `workbook.pdf`. Images are optional
and opt-in (`--generate-images`, via OpenRouter); without them every page prints a
labelled placeholder, so the book is reviewable before any artwork exists.

Python 3.11+, stdlib only for the core generator, web form and image backend. The
one opt-in dependency is `playwright` (+ a Chromium build), needed only for `--pdf`.

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

# Real artwork (needs OPENROUTER_API_KEY). --symbol-cache defaults to
# sources/symbols/images, so universal scavenger-hunt symbols are generated
# once, across every book, ever — not just within one run. A cache *hit*
# never touches the network, so --generate-images with no key still embeds
# every already-cached symbol for free; only uncached symbols and full-page
# illustrations fail (gracefully, logged, left as placeholders).
python -m src.cli --destination "Prague" --pdf --generate-images

# Refresh the checked-in prompt sources after changing UNIVERSAL_SYMBOLS
python -m src.cli --write-symbol-sources

# Re-derive the matching page's cut-outs and silhouettes after adding symbol
# artwork. Authoring tool: needs pillow, numpy and scipy, which nothing in the
# pipeline does. Existing files are left alone unless --overwrite is passed.
python tools/make_shadow_symbols.py

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
Agent 3  ActivityGenerator plugins  → ActivityDraft   (title, instructions, goal, ImageBrief, [SymbolBrief])
        ↓
Agent 4  PromptGenerator            → image_prompt strings + prompts/*.md + prompts/symbols/*.md
        ↓
Agent 5  MarkdownGenerator          → workbook.md          JSON writer → workbook.json
        ↓
Images   ImageBackend               → images/*.png, images/symbols/*.png       (optional)
        ↓
Layout   HtmlRenderer → PdfRenderer → workbook.html, workbook.pdf              (optional)
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
| `src/qa.py` | Post-generation check: scans a non-English workbook's reader-facing text for stray Latin words. Runs automatically inside `generate_workbook`, exposed as `GenerationResult.language_qa`, printed by the CLI and shown as a notice on the web result page |
| `src/ports.py` | `ImageBackend` / `DocumentRenderer` Protocols — the seams for image generation and PDF |
| `src/image_backends/` | `ImageBackend` implementations. `openrouter.py` calls OpenRouter's unified Image API (default model `openai/gpt-image-1`); `runner.py` drives one over a whole book; `sources.py` pre-renders the universal symbol prompts into `sources/symbols/`. Injectable `transport`, so tests never hit the network |
| `sources/symbols/` | Checked-in, repo-wide symbol cache: `prompts/<key>.md` (regenerate with `--write-symbol-sources`), `images/<key>.<ext>` (drop real artwork in by hand or let `--generate-images` fill it), and the derived `cutouts/` + `silhouettes/` (regenerate with `tools/make_shadow_symbols.py`) |
| `src/symbol_art.py` | Resolves which checked-in drawing — and which variant — each symbol on a page gets. Called by `output_writer`, so committed artwork prints on *every* layout run, not only on `--generate-images` runs |
| `data/destinations/` | Curated destination knowledge packs (`<slug>.json`, `<slug>.<lang>.json`) |
| `data/countries.json` + `src/countries.py` | Shared, checked-in country facts (capital, flag colours, spoken language, currency, continent) keyed by ISO 3166-1 alpha-2. Every value is a vocabulary token, translated through the locale modules (`place.athens`, `colour.blue`, ...) — never display text — so a destination pack names its country in one line (`"country": "GR"`) and any language gets it for free. `src/countries.py` loads it strictly: an unknown token or a duplicate code raises, the same posture as `src/symbols/loader.py`. Feeds the quiz's capital/flag/language/continent/currency questions (`src/activities/quiz.py`); a destination with no `country` degrades to its knowledge-based questions instead of guessing |
| `data/phrasebook/` + `src/phrasebook.py` | Curated ten-word phrasebooks, one file per language (`el.json`, `cs.json`, `he.json`, `en.json`), each concept's native word plus a pronunciation spelled in the *workbook's* own script. Feeds the quiz page's dictionary section. Omitted — never printed half-filled — when the destination speaks the workbook's own language, no pack exists for it, a pronunciation is missing, or the script has no embedded font (see `src/fonts.py` below) |
| `src/fonts.py` | The embedded-font manifest: every `@font-face` this project ships, tagged with the script it covers. Base UI faces (Baloo 2, Nunito, Secular One, Assistant, JetBrains Mono) are always embedded; Hebrew, Greek, Cyrillic and Latin-Extended (Noto Sans cuts, for Czech's `ě`/`ř`/`č`) are embedded only when a book's *rendered markup* actually needs them (`scripts_in()`, called from `HtmlRenderer.render`) — so an English book never carries Hebrew type and vice versa. `TemplateSet.font_faces()` raises rather than silently skipping a declared face with no file on disk. `tests/test_fonts.py` is the coverage contract: every shipped phrasebook's script must have an embedded face, checked against the real font files when `fontTools`+`brotli` are installed |

### Activity plugin contract (`src/activities/base.py`)

Adding an activity is **one new file, no other edits** — `src/activities/__init__.py`
auto-discovers every module in the package via `pkgutil` and each module registers
itself with `@register_activity`. A subclass of `ActivityGenerator` declares
`activity_type`, `min_age`/`max_age`, `energy` ("calm"/"active", used to alternate
pages), `required_knowledge` (categories checked by the default `supports()`), and
implements `generate(context, planned) -> ActivityDraft` using the `self.draft(...)`
and `self.pick(...)` helpers. Files prefixed with `_` (e.g. `_wordbank.py`) are shared
helpers, not activities, and are excluded from auto-discovery.

Two activities need no illustration at all — their working area is generated in
Python and typeset directly by the print layout — and both fit real data (a
carved maze, a lettered grid) into a fixed print box without letting content
dictate the box's size:

- **`maze`** (`src/activities/_maze.py` + `maze.py` + `@layout("maze")`). A
  perfect maze is a spanning tree, carved by randomized DFS — `generate_maze()`
  always returns a *fully enclosed* rectangle (a test pins this), because that
  keeps the carve itself simple and correct. The activity then calls
  `open_boundary()` to knock down just the start cell's north wall and the goal
  cell's south wall, and the layout draws the start/goal symbols in their own
  boxes *outside* the grid rectangle (wider than the doorway itself, so a small
  icon has breathing room) rather than overlaid on a corner cell. The maze walls
  are drawn as disconnected per-segment SVG subpaths (`wall_segments()`), so
  `stroke-linecap: square` is required, not decorative — `round` caps on
  unconnected segments bulge at every corner where two walls happen to meet.
- **`word_search`**. The grid is real letters in real cells; `.puzzle-grid`
  (`book.css`) is sized with CSS container queries against `.puzzle-stage`
  (`min(100cqw, 100cqh × aspect-ratio)`), not by letting each cell's own
  `aspect-ratio` set its size from the grid's *width* share alone — that
  earlier approach made the required height come out to roughly the page's
  content width regardless of row count, which fit some difficulties by luck
  and overflowed others. Font size is `clamp()`ed against the same `--cell`
  custom property the grid's own size is computed from, so letters scale with
  the actual rendered cell size instead of staying fixed regardless of grid
  density.

`scavenger_hunt` is a third, unrelated activity that sends the child looking
for real things on the actual trip rather than solving a letter grid — see
below.

### Pages that need many small pictures (`SymbolBrief`)

Most pages need one illustration, described by one `ImageBrief`. A page whose
working area is a **table of pictures** returns a tuple of `SymbolBrief`s instead
(`self.draft(..., symbols=...)`), and Agent 4 renders one prompt per symbol from
`src/templates/symbol_prompt.tmpl`. `scavenger_hunt` is the worked example (and
`matching` is the second — see below), and the reasoning generalises to any grid
page:

- **The table is typeset, never drawn.** The grid, the checkboxes and the words
  are page furniture built by `@layout("scavenger_hunt")` in `src/rendering/layouts.py`.
  Asking one prompt for "a grid of twelve labelled cells, each with an empty
  checkbox" is asking an image model for precisely what it is worst at.
- **One subject per prompt.** A symbol prompt carries no destination, no recurring
  characters and no A4 page geometry — just one object on white. A wrong cell then
  costs one cheap retry instead of the whole page.
- **`SymbolBrief.key` is a language-independent cache key.** It is slugified from
  the *English* term (`slugify` falls back to the literal `"destination"` for a
  string with no Latin letters, so `_symbols.py` guards on the source text before
  slugifying — without that, every untranslated entry would collide onto one key
  and silently share one wrong drawing). Because a universal symbol's prompt is
  byte-identical in every book, `prompts/symbols/<key>.md` and the drawing it
  produces are shared across pages, languages and destinations — point
  `--symbol-cache` at one directory and each symbol is paid for once, ever.
- **Symbol slugs are exempt from the language QA** (`symbol_keys` in `_SKIP_KEYS`,
  `src/qa.py`) because they are deliberately English in every language. The
  reader-facing labels live in `metadata["items"]` and *are* scanned.

The item pool matters as much as the mechanics: a hunt built only from a
destination's landmarks and wildlife is unfinishable, because those things appear
once if at all. `src/activities/_symbols.py` therefore carries `UNIVERSAL_SYMBOLS`
— stop sign, bridge, police car, and other things findable anywhere — and mixes in
only a few destination sights. Easy hunts are entirely universal; harder ones lean
more on the real trip. Universal symbols are translated per locale under
`symbol.<key>`, looked up with `Strings.optional()` so a missing translation
degrades to English rather than crashing a book (a test enforces completeness).

**Grid size is fixed at 4 columns** (`GRID_COLUMNS` in `_symbols.py`); row count
follows from the item count via `grid_dimensions()`. Every difficulty is 16 items
(4×4) — small enough for a 4-year-old to finish, and the one shape the print
layout (`.spotting` in `book.css`) is tuned for: `grid-template-rows` is explicit
rather than content-sized, so a full sheet ends exactly at the bottom of the page.
(An earlier version grew `medium`/`hard` to 20 (4×5); that size was never actually
checked against the print layout and did overflow onto the next page in practice —
`test_no_page_overflows_its_sheet` in `tests/test_rendering.py` now measures every
page's real rendered layout in headless Chromium so that can't happen silently
again.)

**`sources/symbols/`** is the checked-in, repo-wide version of that cache —
`python -m src.image_backends.sources` (or `--write-symbol-sources`) renders every
`UNIVERSAL_SYMBOLS` prompt to `sources/symbols/prompts/<key>.md` once, so a fresh
clone already has them without generating a book first. `sources/symbols/images/`
is where real artwork gets dropped in as `<key>.<ext>`; the CLI's `--symbol-cache`
defaults to that directory, so every run both reuses what's already there
(`generate_symbol_images(..., reuse_existing=True)` in `src/image_backends/runner.py`
picks up any `<key>.*` file already present) and adds whatever it generates back to
the same shared pool. Regenerating the prompts must stay byte-identical to what the
normal pipeline would produce — `test_a_written_prompt_matches_what_the_pipeline_would_generate`
in `tests/test_image_backend_sources.py` pins that.

### Derived symbol art, and the shadow matching page

`matching` ("Match the Shadows") is built from the same per-symbol drawings, for
a reason specific to the puzzle: a shadow only works if it is the *same* shape at
the *same* size as its partner, and the two columns have to disagree about the
order. A single generated illustration of "six things and their silhouettes" gets
neither reliably. Deriving both columns from one cached drawing makes both
guarantees arithmetic.

`tools/make_shadow_symbols.py` (Pillow + numpy + scipy, an authoring tool — nothing
under `src/` imports it, so the stdlib-only rule still holds) turns each
`sources/symbols/images/<key>.png` into two variants that share one crop box:

- `cutouts/<key>.png` — the ruled border detected and erased, cropped to the ink,
  white paper replaced with transparency, stroke antialiasing kept.
- `silhouettes/<key>.png` — that shape flood-filled mid-grey, **outline plus the
  white it encloses**. The fill has to happen here rather than in CSS: a filter
  can only recolour ink that already exists, and a bicycle's silhouette is mostly
  pixels the source drawing left white.

The border is found by shape, not position (a component spanning most of the sheet
whose pixels all sit in a thin band around its own bounding box) because the rules
on these sheets are inset anywhere from 30px to 157px. A drawing whose strokes
*touch* its border merges into one component, fails that test, and is left alone
with a warning rather than erased — the run report and the `_contact.png` index
sheet in each output directory are the review pass.

The matching page uses the universal symbol bank only. A destination sight with no
committed artwork would print as a placeholder in the drawing column and a blank in
the shadow column, so `tests/test_activities.py::UNIVERSAL_ACTIVITIES` exempts it
from the destination-awareness contract.

### Knowledge providers (`src/agents/destination_agent.py`)

`--provider` selects a chain, tried in order, with the offline heuristic always
topping up any empty category so activities can rely on their `required_knowledge`:
`file` (curated JSON packs), `llm` (Claude via `urllib`, injectable `transport` so
tests never hit the network, degrades to `file` on any error), `auto` (default: file
first, LLM only if no pack exists), `heuristic` (generic, always succeeds).

`DestinationKnowledge.country` is a sibling of `KNOWLEDGE_FIELDS`, not a member of
it — an ISO 3166-1 alpha-2 reference into `data/countries.json` (see the `data/`
table above), not a tuple of short strings, so it is deliberately exempt from
`coverage()`, `is_empty`, `filled_with()` and the LLM prompt's field list. The
heuristic provider never sets one (a guessed capital would be worse than the quiz
question not appearing); the LLM provider may *select* a code but never supply its
facts — a code with no `data/countries.json` entry is dropped after the fact.

### Print layout (`src/rendering/`)

`HtmlRenderer` turns `workbook.json` into print-styled A4 HTML; `PdfRenderer` prints it
with headless Chromium via Playwright. The layout adds no content — it typesets what
activities already recorded in page metadata (checkboxes, quiz options, maze grids,
word search cells, etc.), which is why activities keep text **out** of illustrations.
A bespoke per-activity-type page layout is a `@layout("your_type")` function in
`src/rendering/layouts.py` plus a template; anything without a registered layout falls
back to a full-page illustration frame automatically. The PDF renders without a
table of contents (`HtmlRenderer(include_contents=False)` in `output_writer.py`);
standalone HTML output keeps it.

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
