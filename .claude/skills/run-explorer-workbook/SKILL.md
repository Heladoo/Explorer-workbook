---
name: run-explorer-workbook
description: Build, run, and smoke-test the Explorer Workbook generator — CLI (python -m src.cli), the local web form (python -m src.web), and the --pdf/--html print pipeline. Use to run, start, build, test, or screenshot this app, or to confirm a code change works in the real generator/web-form/PDF output rather than just in pytest.
---

Paths below are relative to the repo root (the directory containing `src/`,
i.e. `Explorer-workbook/`), **not** to this skill directory.

Two surfaces:

- **CLI** (`python -m src.cli`) — the surface most changes actually touch
  (agents, activities, rendering). Stdlib only, no setup needed.
- **Web form** (`python -m src.web`) — a thin wrapper over the same
  pipeline, for humans; drive it with `chromium-cli` or plain `curl`/HTTP.

`--pdf`/`--html` need Playwright + a Chromium build; both were already
installed in this container (`python -m playwright --version` → 1.61.0) —
if missing elsewhere, `pip install playwright && playwright install chromium`.

## Prerequisites

Python 3.11+ (verified here on 3.14.6). No `pip install` needed for the
core CLI/web paths — the generator, activities, agents, and web form are
stdlib-only. Playwright is only needed for `--pdf`/`--html`.

## Run (agent path) — the driver

```bash
python .claude/skills/run-explorer-workbook/driver.py
```

This is the harness: it generates a workbook via the CLI (json/md/prompt
files), regenerates it with `--pdf` to exercise the Playwright layout
stage, then spins up `python -m src.web` on port 8091, hits `GET /`, and
checks the form markup — tearing the server down afterward. Exits non-zero
on the first failed check; sample output is left under a temp dir printed
at the end (not auto-deleted) for manual inspection of `workbook.pdf` /
`workbook.html`.

Ran clean in this container:

```
== 1. CLI generation (json/md/prompts) -> ...\prague
  [ok] workbook.json written
  [ok] workbook.md written
  [ok] prompts/ has files
== 2. HTML + PDF layout (--pdf, needs playwright)
  [ok] workbook.html written and non-trivial
  [ok] workbook.pdf written and non-trivial
== 3. Web form smoke (python -m src.web)
  [ok] GET / returns 200
  [ok] form page has the submit button
All checks passed.
```

### Driving the web form interactively (chromium-cli / browser tool)

For anything beyond the smoke check — filling the form, checking the
result page, uploading a photo — start the server and point a browser at
it:

```bash
python -m src.web --port 8000 &
```

then navigate to `http://127.0.0.1:8000`, fill the "Where are you going?"
field (`<input>` under the "Where are you going?" label), click the
`<button type="submit">` (its label is **A/B-tested** — text varies
between "Build it" / "Make my book" per visitor cookie, don't match on
it), and the result page links `workbook.pdf`, `workbook.html`,
`workbook.json`, `workbook.md`, and one `prompts/*.md` per page —
served at `/go/<slug>/<file>`. Verified live in this container: filled
"Prague", submitted, landed on `/go/prague/...` with all 34 prompt files
listed and a working `workbook.pdf` link.

Kill the server when done — it has no shutdown endpoint:

```bash
# find the PID bound to the port, then stop it
```
On Windows: `Get-NetTCPConnection -LocalPort 8000 | Select OwningProcess`
then `Stop-Process -Id <pid> -Force`. On Linux/macOS: `lsof -ti:8000 | xargs kill`.

## Direct invocation (no server/CLI needed)

Most logic lives in `src.api.generate_workbook`, importable directly —
this is what most PRs actually want to exercise:

```python
from src import generate_workbook
result = generate_workbook(destination="Prague", children=["Noa"], ages=[5], page_count=6, seed=42)
print(result.output_dir, result.workbook.page_count)
```

## Run (human path)

```bash
python -m src.cli --destination "Prague" --pdf          # → output/prague/workbook.{json,md,html,pdf}
python -m src.web                                       # → http://127.0.0.1:8000, Ctrl-C to stop
```

## Test

```bash
python -m pytest
```

5 tests were already failing in this checkout before any change of ours,
all in localization/symbol-pack consistency
(`test_localization.py`, `test_scavenger_hunt.py::test_a_hebrew_hunt_keeps_english_keys_and_english_prompts`,
`test_symbols.py::test_translated_packs_carry_an_identical_profile_to_the_base_pack`)
— looks like an in-progress destination pack edit, not something this
skill's driver touches. Don't assume a red run here means your change
broke something; diff against a clean-checkout baseline run first.

## Gotchas

- **`--seed` matters for reproducibility** — omit it and every run
  picks different random content (word search words, quiz answers,
  scavenger items), which makes before/after diffing noisy.
- **The web form's CTA text is A/B-tested** (`src/experiments.py`,
  deterministic hash of the `visitor` cookie) — never assert on its
  literal string; assert on `type="submit"` or the form's other fields
  instead.
- **`--pdf` implies `--html`** and needs Playwright's Chromium build;
  it silently degrades to json/md-only output on any Playwright error
  in some code paths, so check `workbook.pdf` actually exists rather
  than trusting the exit code alone.
- **`output/` is not disposable** — `output/kfar-hanokdim/` is a
  committed sample run (CLAUDE.md is explicit about this). Write smoke
  runs to a temp directory via `--out`, as the driver does, rather than
  the default `output/<slug>`.
- **Symbol images are a shared, repo-wide cache** at
  `sources/symbols/images/` (`--symbol-cache` default) — a smoke run
  without `--generate-images` never touches it, but don't point ad hoc
  test output at that directory.
- **The web server has no `/shutdown` route** — it's a bare
  `http.server`; stop it by killing the process that bound the port
  (see above), not by hitting an endpoint.

## Troubleshooting

- `ModuleNotFoundError: playwright` on `--pdf` → `pip install playwright
  && playwright install chromium`. Not needed for plain CLI/web-form use.
- Web form `GET /` hangs or connection-refused right after starting →
  the server takes a moment to bind; poll rather than firing one request
  immediately (the driver retries for up to 10s).
