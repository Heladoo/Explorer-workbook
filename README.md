# AI Travel Activity Book Generator

Generates a printable children's travel activity workbook for **any** destination —
as data, not as a PDF. Give it a place (and optionally the children's names, ages,
itinerary and interests) and it produces:

| Artifact | What it is |
| --- | --- |
| `workbook.json` | The full workbook structure: every page, its instructions, metadata and final image prompt. |
| `workbook.md` | The human-readable build specification: page number, activity type, educational goal, instructions, required illustration, image prompt and estimated age. |
| `prompts/NN_<activity>.md` | One file per page containing **only** the image prompt, ready to paste into GPT Image, DALL·E, Midjourney or Flux. |
| `prompts/symbols/<slug>.md` | One file per small picture on a table-style page (the scavenger hunt grid). Each asks for a single object, and is identical in every book — so a drawing of a stop sign is generated once and reused forever. |
| `images/` | Optional: the generated artwork, when you ask for it. |
| `workbook.html` / `workbook.pdf` | Optional: the book laid out for print, from HTML/CSS page templates. A5 pages by default. |
| `workbook-booklet.pdf` | Optional: the same pages imposed onto A4 sheets — print duplex, fold once, staple the fold. |

Artwork is opt-in (`--generate-images`, via OpenRouter). Without it every page
prints a labelled placeholder naming its prompt file, so the whole book is
printable and reviewable before a single image exists.

## Quickstart

Python 3.11+. The generator itself has no dependencies; the PDF stage needs
Playwright and a Chromium build.

**A web form, if you'd rather not use the CLI:**

```bash
python -m src.web          # then open http://127.0.0.1:8000
```

Four fields, and only the first is required:

| | |
| --- | --- |
| **Where are you going?** | The one thing we genuinely need. |
| **What's the plan?** | Optional itinerary, one line per day — pages follow along. |
| **Who's coming?** | Optional photos. Every image prompt then asks for children who look like them, and names the files to attach. |
| **Which language?** | English or עברית. |

Everything else the generator decides: 12 pages, curated facts where we have
them, difficulty ramping across the book, and a PDF when a browser is available.
Stdlib `http.server` only, bound to localhost; photos never leave the machine.
The CLI still exposes the full set of options.

**Or the CLI:**

```bash
# --pages takes 8, 12 or 16 — every one a multiple of 4, because one folded
# A4 sheet carries exactly four A5 pages.
python -m src.cli --destination "Kfar Hanokdim" --children Noa,Amit --ages 5,7 --pages 12
# → output/kfar-hanokdim/{workbook.json, workbook.md, prompts/*.md}

python -m src.cli --destination "Kfar Hanokdim" --children Noa,Amit --ages 5,7 --pdf
# → the same, plus workbook.html, an A5 workbook.pdf, and workbook-booklet.pdf:
#   3 A4 sheets to print duplex, fold in half and staple through the fold.
```

From Python:

```python
from src import generate_workbook

result = generate_workbook(
    destination="Kfar Hanokdim",
    children=["Noa", "Amit"],
    ages=[5, 7],
)
print(result.output_dir)          # output/kfar-hanokdim
print(result.workbook.page_count) # 12
```

A sample run is committed under [`output/kfar-hanokdim/`](output/kfar-hanokdim) if
you just want to read the artifacts.

Useful flags:

```bash
--language en              # workbook language (image prompts stay English)
--difficulty easy          # force one difficulty instead of ramping
--interests animals,trains # bias activity choice and page focus
--itinerary "Day 1,Day 2"  # ground pages in the real trip
--provider auto|file|llm|heuristic
--seed 42                  # reproducible output
--list-destinations        # which places have a curated data pack
--html                     # lay the book out for print, no browser needed
--pdf                      # print it to PDF (implies --html)
--format a5-booklet|a4-portrait   # A5 folded booklet (default), or one page per A4 sheet
--no-booklet               # A5 pages only; skip the imposed fold-and-staple sheets
--generate-images          # draw the artwork (needs OPENROUTER_API_KEY)
--image-model <slug>       # which model draws it (default: openai/gpt-image-1)
--symbol-cache <dir>       # shared symbol drawings (default: sources/symbols/images)
--write-symbol-sources     # (re)write sources/symbols/prompts/*.md, then exit
```

## Languages

`--language he` produces a Hebrew workbook: translated copy, a right-to-left
printed page, and a Hebrew word search grid. **Image prompts stay English** wherever the workbook goes, because that
is what image models are trained on — a translated pack carries an
`illustration_terms` map and the locale carries a `TERMS` map, and the prompt
generator uses them to put the English noun back before rendering. The
destination's canonical name, slugs and filenames stay English too; only what the
child reads is translated.

Two files make a language:

- `src/locales/<code>.py` — `LANGUAGE`, optional `DIRECTION = "rtl"`, `STRINGS`
  (same keys as `en.py`), optional `TERMS` for copy that reaches an image prompt.
- `data/destinations/<slug>.<code>.json` — a translated pack, with
  `display_name` and `illustration_terms`. Optional: without it the pages use
  the base pack's English facts and only the copy is translated.

## How it works

Five agents, one shared immutable `WorkbookContext`, activities as plugins.
Nothing skips ahead, and no activity talks to another activity.

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

Activities return a **structured `ImageBrief`**, not prompt text. Agent 4 is the only
component that knows how prompts are worded, so the entire book's illustration style
can be changed in one place (`StyleGuide` + `src/templates/style_guide.tmpl`) without
touching a single activity.

| Path | Responsibility |
| --- | --- |
| `src/models/` | `WorkbookContext`, `DestinationKnowledge`, `PlannedPage`, `ImageBrief`, `Page`, `Workbook` |
| `src/agents/` | The five agents |
| `src/activities/` | One module per activity, auto-discovered |
| `src/locales/` | User-facing copy, one module per language |
| `src/templates/` | Style guide and markdown templates |
| `src/templates/pdf/` | Print page templates and `book.css` |
| `src/rendering/` | Layout stage: workbook → printable HTML → PDF |
| `src/web.py` | Local web form (`python -m src.web`) |
| `src/uploads.py` | Multipart parsing for the photo upload |
| `src/templates/web/` | The form, result page and their CSS |
| `src/pipeline.py` | Wires the agents together (all injectable) |
| `src/output_writer.py` | The only module that touches the filesystem |
| `src/ports.py` | `ImageBackend` / `DocumentRenderer` — the seams for images and PDF |
| `src/image_backends/` | Image generation via OpenRouter, and the runner that drives it |
| `data/destinations/` | Curated destination packs |

### Where the facts come from

`--provider` picks the chain; whatever it produces, empty categories are topped up
by the offline heuristic provider so activities can rely on the knowledge they declare.

- **`file`** — curated JSON packs in `data/destinations/` (exact, offline).
- **`llm`** — asks Claude for the same JSON shape (`ANTHROPIC_API_KEY` required); falls
  back to packs if the key is missing or the call fails.
- **`auto`** (default) — packs first, model only when there is no pack.
- **`heuristic`** — generic travel material only. Always works, and the workbook says
  plainly that its content is generic.

Nothing is hardcoded per destination in the generators: every page's content comes
from whatever the knowledge provider returned.

## Extending it

**Add an activity** — one file, no other edits:

```python
# src/activities/postcard.py
from src.activities.base import ActivityGenerator, ImageBrief, RenderMode, register_activity

@register_activity
class PostcardActivity(ActivityGenerator):
    activity_type = "postcard"
    display_name = "Write a Postcard"
    educational_goal = "Practises writing for a reader and choosing what is worth telling."
    min_age, max_age = 6, 12
    energy = "calm"
    required_knowledge = ("landmarks",)

    def generate(self, context, planned):
        subject = self.pick(context, "landmarks", 1, salt=planned.number)[0]
        return self.draft(
            title=f"A Postcard from {context.destination}",
            instructions=f"Draw {subject} on the front, then write to someone at home.",
            planned=planned,
            image_brief=ImageBrief(
                subject="a blank postcard, front and back",
                render_mode=RenderMode.FRAME,
                composition="Top half: an empty framed picture area. Bottom half: "
                            "an address panel with ruled lines and a stamp box.",
            ),
            metadata={"subject": subject, "writing_lines": 6},
        )
```

The package auto-discovers it, the planner starts scheduling it, and the prompt and
markdown generators handle it without knowing it exists.

**Add a language** — see [Languages](#languages) above; `src/locales/he.py` is a
worked example.

**Add a destination pack** — drop a JSON file in `data/destinations/` with the eight
knowledge categories (see `kfar-hanokdim.json`).

**Change how a page prints** — edit the HTML template in `src/templates/pdf/` or
`book.css`. A new bespoke page layout is one `@layout("your_type")` function in
`src/rendering/layouts.py` plus a template; an activity with no registered layout
prints as a full-page illustration frame, so new plugins work untouched.

**Use a different image model** — `src/image_backends/openrouter.py` implements
`ImageBackend` from `src/ports.py` against OpenRouter's unified Image API, so any
model it serves is `--image-model <slug>`. A different provider entirely is a new
class implementing the same Protocol; its `transport` is injected, so tests never
touch the network.

Neither requires changing an agent or an activity.

## Images

```bash
export OPENROUTER_API_KEY=...
python -m src.cli --destination "Prague" --pdf --generate-images
```

Every page's `image_prompt` is already final, so generation is a separate pass
over finished data: one call per page, plus one per distinct symbol. A page that
fails to render is logged and skipped — it keeps its placeholder frame, and the
rest of the book still comes out.

`--symbol-cache` is the interesting flag, and defaults to `sources/symbols/images/`.
The small pictures on the scavenger hunt grid are drawn from prompts that mention
no destination, no characters and no house style, which means **the same drawing
is correct in every book**. Point every run at one directory (the default already
does this) and each symbol is paid for once, ever; a Hebrew book and an English
book share the same files, because the cache key is slugified from the English
term while only the printed label is translated.

```bash
python -m src.cli --write-symbol-sources
```

writes every universal symbol's prompt to `sources/symbols/prompts/<key>.md` —
checked into the repo, so a fresh clone already has them without generating a book
first. Drop real artwork into `sources/symbols/images/` as `<key>.<ext>` (by hand,
or let `--generate-images` fill it in) and every future book reuses it automatically.
See [`sources/symbols/README.md`](sources/symbols/README.md).

Reference photos flow through automatically: when they were supplied, the page
prompts already ask for those children, and the backend attaches
`context.family_photos` to the request. Symbol requests deliberately don't attach
them — a stop sign has no people in it, and keeping the request identical
everywhere is what makes the drawing reusable.

## Print layout

`--html` and `--pdf` run the layout stage: `HtmlRenderer` turns `workbook.json` into a
print-styled document, and `PdfRenderer` prints it with headless Chromium. The
layout adds no content — it arranges what the activities already recorded.

Two formats. **`a5-booklet`** is the default: A5 pages, printed two-up on A4, folded
once and stapled through the fold — so `--pdf` writes both `workbook.pdf` (the pages
in reading order) and `workbook-booklet.pdf` (the same pages on sheets, ready to
print duplex). **`--format a4-portrait`** keeps the original one-page-per-sheet
layout, which needs no folding, no stapler and no duplex printer.

The A5 pages are laid out natively at A5, not shrunk from A4 — booklet-printing an A4
layout scales it to 70.7%, which takes body copy to 8.1pt and the writing lines with
it, below what a five-year-old can write on. The type scale is re-tuned instead.

One page can be a **double-page centre spread** — the route map, when the trip has a
real itinerary to draw. That is the only place a spread can go: for an `N`-page
saddle-stitched book the innermost sheet's back side is exactly pages `N/2` and
`N/2+1`, the only pair that shares one side of one sheet.

That is why activities keep text **out** of the illustrations: the page metadata
becomes real page furniture. Packing checkboxes and item names, quiz questions with
lettered answer bubbles, matching columns in their planned order, reflection prompts
with ruled lines and one star per trip day are all typeset by the layout, so the
illustration stays a wordless picture that any image model can draw. A few pages —
the maze, the quiz — carry no illustration at all beyond an optional decorative
border, because their working area is entirely typeset text or generated geometry.

Pages without artwork print a labelled placeholder frame naming their prompt file, so
the book is printable and reviewable before a single image exists.

```bash
pip install .[pdf]   # or: pip install playwright
                      # Chromium must be available; set CHROMIUM_EXECUTABLE if it
                      # lives outside the usual Playwright browsers directory
```

`--html` needs neither. If Playwright or Chromium is missing, `--pdf` fails with an
explanation and everything else still works.

## Analytics, experiments & feedback

`python -m src.web` also tracks how the form is doing, deliberately the dull way:
events are appended to a JSONL file next to the generated books
(`output/.analytics/events.jsonl`), there are no third-party beacons, no IP
addresses are stored, and the only identifier is a random value in a first-party
`visitor` cookie. `AnalyticsSink` (`src/analytics.py`) is a `Protocol`, so pointing
this at a real analytics service later is a new class, not a rewrite — the same
seam as `ImageBackend` and `DocumentRenderer` in `src/ports.py`. Run with
`--no-analytics` to disable it entirely; nothing is written to disk.

Open `http://127.0.0.1:8000/stats` for the report:

- **Funnel** — distinct visitors who opened the form, submitted it, got a book,
  and opened what they got, each as a share of the step before and of the top.
- **Conversion rate** — books made as a share of people who opened the form.
- **A/B results** — see below.
- **Feedback** — the tally of 🙌/🙂/😕 ratings plus the last few comments.
- **Destinations** — what people are actually asking for.

**A/B testing** (`src/experiments.py`) needs no server-side state: a visitor's
variant is `sha256(f"{experiment_key}:{visitor_id}")`, so the same visitor always
lands in the same arm and different experiments never influence each other.
Two are live right now:

| Experiment | Variants | Question |
| --- | --- | --- |
| `cta` | `make_my_book` / `build_it` | Does a more concrete call to action get more books made? |
| `optional_fields` | `visible` / `tucked` | Do the optional fields help, or do they scare people off? |

Each visitor's assignment travels on their `form_view`, `form_submitted` and
`book_created` events, so the stats page can compute per-variant conversion and
lift against the control without ever storing a visitor→variant table. Add an
experiment by adding an `Experiment(...)` to `ACTIVE` — nothing else changes.

**Feedback**: the result page ends with a three-tap rating and an optional
comment, sent with a plain `fetch()` to `/feedback` — no page reload, no
framework, and a failed request is swallowed silently so a flaky network never
looks like a broken book.

## Activities

`cover`, `coloring`, `maze`, `spot_difference`, `hidden_objects`, `scavenger_hunt`,
`packing`, `matching`, `wildlife_facts`, `quiz`, `word_search`, `drawing`,
`reflection`.

**`word_search` needs no illustration at all.** The grid is generated here — every
listed word genuinely findable, orthogonal at easy, diagonal and reversed at
harder levels — and travels in the page metadata for the layout to typeset. Its
image prompt is an optional decorative border, so it costs nothing to produce
beyond the text.

**`scavenger_hunt` sends the child looking at the real world, not a drawing of
it.** Unlike `hidden_objects` (things tucked into an illustrated scene), this is
a grid of pictures to tick off as the child genuinely spots each thing.

Two things make it work, and both go against how the rest of the book is drawn:

- **The table is typeset, not drawn.** The grid, the boxes and the words are
  built by the print layout. A single prompt asking for "twelve labelled cells,
  each with an empty checkbox" is asking an image model for exactly what it is
  worst at — exact counts, one specific thing per cell, and no stray text.
- **Each picture is its own prompt** (`prompts/symbols/<slug>.md`), asking for one
  object on white. That is what image models are reliable at, and a cell that
  comes out wrong costs one cheap retry instead of a ruined page.

The items are mostly **ordinary**, too. A hunt built only from a destination's
landmarks and wildlife is unfinishable — those things appear once, if at all. So
most cells are everyday sights a child can find on the way to anywhere (a stop
sign, a bridge, a police car, a dog on a lead), and a few come from the
destination so the page still belongs to this trip. An easy hunt is entirely
everyday things; harder ones lean more on the real place.

The grid is fixed at **4×4 = 16 items**, every difficulty, sized to fill a
page without spilling onto a second one. Rows are sized explicitly in the print
CSS, not left to grow with content, so a full sheet always ends exactly at the
bottom of the page.

The planner opens with the cover, closes with the reflection page, ramps difficulty
across the body, caps difficulty by the youngest child's age, alternates quiet and
active pages, rotates the knowledge category each page leans on, spreads the itinerary
across the book, and drops any activity whose `supports()` says the destination or the
ages do not suit it.

## Tests

```bash
pip install pytest
python -m pytest
```

362 tests covering the plugin contract (every activity, every difficulty), planner
rules, the style contract every prompt must satisfy, all three knowledge providers
(the LLM one with an injected transport, never the network), image generation
(request shape, base64 decoding, per-symbol prompts, the reuse cache, and that one
failure never costs the rest of the book — all through injected transports), the
scavenger hunt end to end (an easy sheet is entirely everyday things, symbol keys
stay identical across languages so one drawing serves every book, the grid is
typeset rather than drawn), the generated puzzles
(the tests solve them — every listed word is searched for in the grid), Hebrew end to end (translated
copy with English prompts, RTL markup, Hebrew word-search grids), the web form
(the four-field flow, photo uploads and how they reach the prompts, multipart
parsing, bad input, escaping, path-traversal), the print layout
(structure, escaping, per-activity furniture, placeholder-to-artwork swap), the
end-to-end artifacts including byte-for-byte reproducibility, and analytics/A-B
testing/feedback: assignment stability and even distribution, the report math
(funnel percentages, per-variant conversion and lift, the "no leader when nobody
converted" edge case), and the whole flow through a running server — cookie
issuance, funnel events in order, variant-consistent rendering, feedback
validation, and the `/stats` page itself. The two PDF tests skip themselves when
Chromium is unavailable.
