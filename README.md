# AI Travel Activity Book Generator

Generates a printable children's travel activity workbook for **any** destination —
as data, not as a PDF. Give it a place (and optionally the children's names, ages,
itinerary and interests) and it produces:

| Artifact | What it is |
| --- | --- |
| `workbook.json` | The full workbook structure: every page, its instructions, metadata and final image prompt. |
| `workbook.md` | The human-readable build specification: page number, activity type, educational goal, instructions, required illustration, image prompt and estimated age. |
| `prompts/NN_<activity>.md` | One file per page containing **only** the image prompt, ready to paste into GPT Image, DALL·E, Midjourney or Flux. |
| `workbook.html` / `workbook.pdf` | Optional: the book laid out for print on A4, from HTML/CSS page templates. |

No images are generated — that stage is still a seam, see [Extending it](#extending-it).

## Quickstart

Python 3.11+. The generator itself has no dependencies; the PDF stage needs
Playwright and a Chromium build.

```bash
python -m src.cli --destination "Kfar Hanokdim" --children Noa,Amit --ages 5,7 --pages 12
# → output/kfar-hanokdim/{workbook.json, workbook.md, prompts/*.md}

python -m src.cli --destination "Kfar Hanokdim" --children Noa,Amit --ages 5,7 --pdf
# → the same, plus workbook.html and a printable A4 workbook.pdf
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
--pdf                      # print it to A4 PDF (implies --html)
```

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
| `src/pipeline.py` | Wires the agents together (all injectable) |
| `src/output_writer.py` | The only module that touches the filesystem |
| `src/ports.py` | `ImageBackend` / `DocumentRenderer` — the seams for images and PDF |
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
# src/activities/word_search.py
from src.activities.base import ActivityGenerator, ImageBrief, RenderMode, register_activity

@register_activity
class WordSearchActivity(ActivityGenerator):
    activity_type = "word_search"
    display_name = "Word Search"
    educational_goal = "Builds vocabulary for local places and animals."
    min_age, max_age = 6, 12
    energy = "calm"
    required_knowledge = ("wildlife",)

    def generate(self, context, planned):
        words = self.pick(context, "wildlife", 6)
        return self.draft(
            title=f"{context.destination} Word Search",
            instructions="Find every animal hiding in the grid.",
            planned=planned,
            image_brief=ImageBrief(
                subject="an empty word search grid",
                render_mode=RenderMode.PUZZLE,
                composition="A 10x10 grid of empty squares.",
            ),
            metadata={"words": list(words)},
        )
```

The package auto-discovers it, the planner starts scheduling it, and the prompt and
markdown generators handle it without knowing it exists.

**Add a language** — drop `src/locales/he.py` with `LANGUAGE = "he"` and a `STRINGS`
dict using the same keys as `en.py`.

**Add a destination pack** — drop a JSON file in `data/destinations/` with the eight
knowledge categories (see `kfar-hanokdim.json`).

**Change how a page prints** — edit the HTML template in `src/templates/pdf/` or
`book.css`. A new bespoke page layout is one `@layout("your_type")` function in
`src/rendering/layouts.py` plus a template; an activity with no registered layout
prints as a full-page illustration frame, so new plugins work untouched.

**Generate real images** — implement `ImageBackend` from `src/ports.py`. Every page's
`image_prompt` is already final; a backend only has to call an image model and save
the result. Pass the files to the renderer as `images={page_number: path}` and the
placeholder frames become the artwork — nothing else changes.

Neither requires changing an agent or an activity.

## Print layout

`--html` and `--pdf` run the layout stage: `HtmlRenderer` turns `workbook.json` into a
print-styled A4 document, and `PdfRenderer` prints it with headless Chromium. The
layout adds no content — it arranges what the activities already recorded.

That is why activities keep text **out** of the illustrations: the page metadata
becomes real page furniture. Packing checkboxes and item names, quiz questions with
answer bubbles, matching columns in their planned order, reflection prompts with
ruled lines and one star per trip day are all typeset by the layout, so the
illustration stays a wordless picture that any image model can draw.

Pages without artwork print a labelled placeholder frame naming their prompt file, so
the book is printable and reviewable before a single image exists.

```bash
pip install playwright   # Chromium must be available; set CHROMIUM_EXECUTABLE if it
                         # lives outside the usual Playwright browsers directory
```

`--html` needs neither. If Playwright or Chromium is missing, `--pdf` fails with an
explanation and everything else still works.

## Activities

`cover`, `coloring`, `maze`, `spot_difference`, `hidden_objects`, `packing`,
`matching`, `wildlife_facts`, `quiz`, `drawing`, `reflection`.

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

163 tests covering the plugin contract (every activity, every difficulty), planner
rules, the style contract every prompt must satisfy, all three knowledge providers
(the LLM one with an injected transport, never the network), the print layout
(structure, escaping, per-activity furniture, placeholder-to-artwork swap), and the
end-to-end artifacts including byte-for-byte reproducibility. The two PDF tests skip
themselves when Chromium is unavailable.
