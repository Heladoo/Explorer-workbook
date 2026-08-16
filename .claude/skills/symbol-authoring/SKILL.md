---
name: symbol-authoring
description: Split a multi-symbol doodle/grid sheet into individual drawings, derive their matching-page cutout + silhouette variants, and register them in the symbol library so they actually appear in generated books. Use when adding/updating scavenger-hunt or matching-page symbol artwork, splitting a sheet of drawings (doodle sheet or evenly-spaced grid) into separate images, regenerating cutouts/silhouettes/shadow art for sources/symbols/, or wiring new artwork into data/symbols/library.json.
---

Paths below are relative to the repo root (the directory containing `src/`),
**not** to this skill directory.

This is an **authoring pipeline**, not part of the app itself — nothing
under `src/` imports `tools/*.py`, so the app's stdlib-only rule still
holds. The tools need Pillow, numpy and scipy (already installed in this
container; elsewhere: `pip install pillow numpy scipy`).

Three stages — split, derive, register — with one required manual step
(picking names) in between the first two:

```
sheet with many symbols on it
        │
        ├─ scattered doodle sheet ──────► tools/split_decor.py
        └─ evenly-spaced grid, each cell already bordered ──► tools/split_grid.py
        │
        ▼  numbered/named crops + _contact.png + manifest.json
        ▼  (human: look at _contact.png, confirm/rename the keepers)
        ▼
sources/symbols/images/<key>.png   ← one file per symbol key
        │
        ▼
tools/make_shadow_symbols.py  → sources/symbols/cutouts/<key>.png
                                 sources/symbols/silhouettes/<key>.png
        │
        ▼  (only if this is a *new* key, not new art for an existing one)
data/symbols/library.json     ← add an entry so the symbol is actually
                                 picked up by scavenger hunts / matching pages
```

**Step 3 (library registration) is easy to forget** — artwork sitting in
`sources/symbols/images/` with no library entry is never used by a
generated book. It's the difference between "I have a PNG" and "I can use
it."

## Run (agent path) — the driver

```bash
python .claude/skills/symbol-authoring/driver.py
```

Exercises `split_decor.py` and `make_shadow_symbols.py` against real
checked-in inputs (`sources/Decor/Pelion/doodle pelion.png`, and the
checked-in `bicycle`/`dog` source drawings), writing only to a scratch temp
dir — it never touches `sources/symbols/` itself. Verified in this
container: it correctly isolated all 34 objects on the Pelion doodle sheet
into individual crops, and produced a clean frame-stripped bicycle/dog
cutout plus a solid-grey bicycle/dog silhouette — inspected both
`_contact.png` sheets by eye, not just checked that files exist.

`split_grid.py` isn't in the driver yet (it was added after, see Gotchas
for why a fixed smoke fixture doesn't fit it well) — run it directly per
Step 1b below; it was verified live in this container against
`sources/symbols/Grid/grid animals.png` (20 cells found, 2 red-marked
cells correctly auto-skipped, all 18 remaining crops matched their
intended animal by eye).

## Step 1a — split a scattered doodle sheet

```bash
python tools/split_decor.py "sources/Decor/Pelion/doodle pelion.png" --dry-run   # list what it would find, write nothing
python tools/split_decor.py "sources/Decor/Pelion/doodle pelion.png"             # → sources/Decor/Pelion/split/doodle-pelion/
```

Finds objects by **connected-component blob detection** (dilate the ink
mask until each drawing's strokes merge into one blob, label components,
crop each tightly) — built for a sheet with objects scattered at odd
angles and no grid to crop on. Output: `symbol_NNN.png` / `band_NNN.png`
crops (a "band" is a long thin run — lettering, a meander border), a
`_contact.png` index sheet, and `manifest.json`.

Useful flags: `--merge` (dilation radius — raise if one drawing splits
into pieces, lower if neighbours fuse; the usable band is narrow — on the
Pelion sheets radius 3 already fuses the whole page, default is 2),
`--pad`, `--min-side`/`--min-ink` (drop specks), `--square`, `-o`.

## Step 1b — split an evenly-spaced grid sheet

**Don't use `split_decor.py` for this** — confirmed on
`sources/symbols/Grid/grid animals.png`: blob-merge dilation fuses each
row's individually-bordered cells into one giant blob per row (each
cell's own frame sits close enough to its neighbours' that they merge).
Use `tools/split_grid.py` instead — it finds the blank rows/columns
*between* cells and cuts exactly there, so it needs no merge-radius
tuning:

```bash
python tools/split_grid.py "sources/symbols/Grid/grid animals.png" --dry-run
python tools/split_grid.py "sources/symbols/Grid/grid animals.png" \
    --labels "owl,dolphins,brown-bear,swallows-nesting,goat,kestrel,squirrel,swan,fox,monkey,camel,horse,cow,nubian-ibex,seal,eagle,turtle,donkey" \
    -o /some/scratch/dir
```

Handles multiple blocks of different sizes on one sheet (a 6×2 block, a
gap, then a 4×2 block — exactly what `grid animals.png` is) by detecting
row-bands and column-bands independently per band, not by assuming one
uniform grid. `--labels` is optional: give it a comma-separated list, in
reading order (row-major, top block before bottom, left to right within a
row), and cells are named and slugified directly — skip it to get
numbered `cell_NNN.png` crops for a manual rename pass instead, same
workflow as `split_decor.py`.

**A solid-red painted cell is auto-detected and skipped** (the sheet's own
"nothing here" marker — `grid animals.png` used it for two reserved
slots). If `--labels` count doesn't match the number of non-skipped cells
found, the tool refuses to write and dumps the row/col listing so you can
see which cell it disagrees with you about. Turn off with
`--no-skip-red` if a sheet doesn't use that convention.

## Step 2 — rename/confirm, then derive the matching-page variants

Whichever splitter you used, **always look at `_contact.png` before
trusting a batch** — even with `--labels` given, a mis-numbered crop is a
silent mislabel, not an error. Move (or leave, if you cropped straight
into place) the reviewed files into `sources/symbols/images/<key>.png`.

```bash
python tools/make_shadow_symbols.py --dry-run        # report what's missing, write nothing
python tools/make_shadow_symbols.py                  # derive everything missing
python tools/make_shadow_symbols.py bicycle dog       # just these keys
python tools/make_shadow_symbols.py --overwrite --grey 140
```

Reads `sources/symbols/images/<key>.png` and writes two variants, both
cropped from the **same box** so a drawing and its shadow print at
identical size on the "Match the Shadows" page:

- `sources/symbols/cutouts/<key>.png` — the ruled border removed (found
  by shape, not position — a component spanning most of the canvas whose
  pixels sit in a thin band around its own bounding box), cropped to the
  ink, transparent background.
- `sources/symbols/silhouettes/<key>.png` — the same shape flood-filled
  solid grey (outline **and** everything it encloses), so interior detail
  a child could match on disappears.

Also writes a `_contact.png` to each output directory — inspect both.
Nothing is deleted; an existing derivative is left alone unless
`--overwrite`.

## Step 3 — register a genuinely new symbol in the library

New artwork for an **existing** key needs nothing further — Step 2 already
overwrote its cutout/silhouette and every book picks it up automatically.
A **brand-new** key (an animal that never existed in the bank before)
needs an entry in `data/symbols/library.json`, or nothing will ever
select it — `src/symbols/loader.py` loads that file strictly (unknown
field or tag value raises) into the `Library` that
`src/activities/_symbols.py::UNIVERSAL_SYMBOLS` (via
`library().universal_pool()`) draws from.

Required fields per entry (`src/symbols/model.py`,
`src/symbols/vocab.py`):

```json
{
  "key": "owl",
  "label": "an owl",
  "subject": "a wide-eyed owl perched on a branch, wings folded",
  "topic": "animals",
  "ubiquity": "common",
  "status": "ready",
  "roles": ["spot", "shadow"]
}
```

- `topic` — one of the closed `TOPICS` in `src/symbols/vocab.py`
  (`street`, `vehicles`, `buildings`, `animals`, `water`, `people`,
  `food`, `gear`, `nature`). Exactly one; it's what keeps two similar
  symbols off the same matching page.
- `ubiquity` — `everywhere` / `common` / `regional` / `local`. Only
  `everywhere`/`common` entries feed `universal_pool()` (the always-findable
  backbone every easy hunt is built from) — a camel or a nubian ibex
  probably wants `regional`, not `everywhere`.
- `status` — `"ready"` once both `images/` and its `cutouts`/`silhouettes`
  exist; `"draft"` if you're registering the key before artwork exists
  (`Library.missing_art()` tracks these).
- `roles` — `spot` (scavenger hunt) and/or `shadow` (matching page) and/or
  `pack` (things you'd actually pack for a trip).
- `subject` is the **English image-generation prompt text** — free-form,
  not a tag. Since artwork for these already exists (hand-drawn, not
  generated from a prompt), it still needs writing for consistency/future
  regeneration, but doesn't have to describe the exact drawing pixel for
  pixel.

This step involves **judgment calls per symbol** (is a seal "everywhere"
or "regional"? does a swallow's nest count as `animals` or `nature`?) —
worth doing as its own pass rather than rushing through a large batch.

## Gotchas

- **A drawing whose strokes touch the ruled border merges into one
  component with it** — frame detection then fails the "hollow rectangle"
  shape test, `make_shadow_symbols.py` reports
  `frame merges with the drawing — left in place`, and the border survives
  into the cutout (then fills the *entire* silhouette solid grey, since
  the un-stripped border reads as one big closed shape). Confirmed on
  `owl` and `monkey` from `grid animals.png` (a perching branch and a
  hanging vine both reach the cell's edge). Fix: the frame in a
  freshly-cropped grid cell sits in a known thin band right at the crop
  edge (not the 30–157px varying inset of the original `images/`
  convention) — whiten just that band (e.g. rows/cols
  `4:14` and `h-14:h-4` / `w-14:w-4` for a cell cropped with
  `split_grid.py`'s default `--pad 4`) before calling
  `make_shadow_symbols.derive()` on the cleaned copy, instead of trying to
  fix the general shape-based detector. There's no flag for this yet —
  it's a one-off numpy patch per affected key; check `_contact.png`
  afterward.
- **Not every drawing's outline closes on its own** — a mountain range, a
  tractor, a train stop mid-air with no baseline, so
  `binary_fill_holes` alone leaves their interior unfilled in the
  silhouette. `GROUND_SIDES` and `EXTRA_CLOSE_RADIUS` in
  `tools/make_shadow_symbols.py` are **per-key allow-lists**, added only
  after checking that key's `_contact.png` silhouette by eye — don't
  apply a global closing radius; it welds shut bicycle spokes and
  sunglasses lenses.
- **Crop numbers/cells are not keys** — a splitter's default output is
  `symbol_007.png` or `cell_003.png`, not `bicycle.png`; confirming names
  against `_contact.png` is mandatory even when `--labels` was given,
  since a miscounted label list silently shifts every name after the
  mismatch.
- **`sources/symbols/` is a shared, repo-wide, accumulating cache** — it
  is committed and reused across every book, language and destination
  (see `sources/symbols/README.md`). Don't point authoring-tool output
  (`-o`, `--cutouts`, `--silhouettes`) at it for experiments; use a
  scratch directory and only copy in what you've actually reviewed.
- **Artwork alone doesn't make a symbol usable** — see Step 3. It's the
  single easiest thing to forget after a successful split + derive.

## Troubleshooting

- `ModuleNotFoundError: No module named 'PIL'` (or `numpy`/`scipy`) →
  `pip install pillow numpy scipy`. None of these tools are part of the
  app's dependency set on purpose.
- A symbol's silhouette comes out as a near-empty outline instead of a
  filled shape → its drawing isn't a closed loop from some edge (see the
  mountain/tractor/train case above); either accept the outline-only
  result or add a `GROUND_SIDES`/`EXTRA_CLOSE_RADIUS` entry after
  eyeballing the contact sheet.
- A symbol's silhouette comes out as a **solid grey rectangle** → its
  source drawing touches the ruled border (see the owl/monkey Gotcha
  above) — the "frame merges with the drawing" case, not a fill-holes
  case.
- `LibraryError` on `load_library()` → an unknown field name or a tag
  value not in `src/symbols/vocab.py`'s closed lists (e.g. a `topic` that
  isn't one of the nine defined ones). The loader is deliberately strict;
  fix the entry rather than trying to widen the vocabulary casually.
