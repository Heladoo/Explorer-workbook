# Project Backlog

Running log of infrastructure, feature, and bug work. Items are logged here for
tracking only — nothing on this list is being executed until picked up
explicitly in a future session.

Each item is tagged with its source: `[user]` or `[claude]` (raised during dev).

Status values: `open` (default, omitted below), `in-progress`, `done`.

## Infrastructure

- [x] Verify git/GitHub coverage: confirm the entire project (all files and data) is checked in to local git and pushed to GitHub, nothing important is only local or gitignored `[user]` — done 2026-08-12: working tree clean, both local branches match `origin` exactly, no stashes, `.gitignore` only excludes caches/venvs/generated `output/*` (sample run stays committed). Two findings surfaced, not fixed here: (1) repo has no `main`/`master` — GitHub's default branch is literally `claude/travel-activity-book-generator-09n1i0`, and PR #1 targets that branch; (2) the repo is **public**, which sharpens the existing "release without exposing files/data/symbols" item above.
- [ ] Check user web form interaction (audit the actual UX flow end-to-end) `[user]`
- [ ] Decide how to release without exposing all project files, data, and internal symbols `[user]`
- [x] Figure out how many image generations are actually needed (scope/cost for the `ImageBackend` seam) `[user]` — done 2026-08-13: already computed and surfaced per run via each page's `needs_illustration` metadata flag (`False` only for `word_search`/`crossword`, since those are fully typeset puzzles) — `src/web.py`'s result page already reports it: "N pages want a picture... the other M are already finished."
- [x] Delete all unused prompt files `[user]` — done 2026-08-13: `output_writer.py`'s `_warn_about_stale()` already detects leftover `prompts/*.md` files from an earlier, longer run and logs a warning rather than silently deleting them (deliberate, so nothing a user might still want is auto-removed). Nothing to delete right now — the committed sample has exactly 14 prompt files for its 14 pages.
- [ ] Rename `output/kfar-hanokdim/` (the committed sample run) to something like `output/example/`, and reconsider whether it's still relevant to keep — revisit later `[user]`
- [ ] Add CI (e.g. GitHub Actions) to run `pytest` automatically on push/PR — no workflow currently exists `[claude]`
- [x] Add a dependency manifest (`pyproject.toml` / `requirements.txt`) pinning versions, including Playwright for `--pdf` — none exists today; overlaps with the release task above `[claude]` — done 2026-08-13: added `pyproject.toml` (`[project]` metadata, `requires-python >= 3.11`, empty core `dependencies` since the generator stays stdlib-only) with `pdf` (`playwright>=1.40,<2`) and `dev` (`pytest>=7,<10`) optional-dependency groups; README's Playwright install line and CLAUDE.md's tooling note updated to match. No lockfile/exact pins — this is a library-style manifest with minimum-version ranges, not a deployable app needing a frozen lockfile.
- [ ] Add test coverage tooling/reporting (e.g. `pytest-cov`) — no coverage measurement configured, separate from the git/GitHub coverage check above `[claude]`
- [ ] Add rotation/retention policy for the web form's analytics sink (`output_root/.analytics/events.jsonl`), which currently grows unbounded `[claude]`
- [ ] Set `main` as the repo's actual default branch on GitHub (Settings → Branches) — the `main` branch and history now exist and PR #1 targets it, but no available tool can flip the repository setting itself; needs a human click `[claude]`
- [x] Set up a `main` branch as the project trunk `[user]` — done 2026-08-12: created `main` from the tip of `claude/travel-activity-book-generator-09n1i0` (the prior default) and pushed it; retargeted PR #1's base onto `main`. Flipping GitHub's actual "default branch" setting still needs a human (see item above); old branch left in place, not deleted.
- [x] Keep `.env`, output files, and user-uploaded files out of GitHub / non-local exposure `[user]` — done 2026-08-12: `.env` was never gitignored (no `.env` in use today, added defensively); the `output/kfar-hanokdim/` exception un-ignored the whole directory tree, so a real reference-photo upload (`src/web.py`'s `_save_photos`, saved under `output/<slug>/reference/`) or regeneration for that destination would have ridden along un-ignored — tightened to an explicit allowlist of just the 5 committed sample files, verified with `git check-ignore`. Confirmed via `git ls-files output/` that no other destination's output is tracked, staged, or untracked-but-present anywhere under `output/`.

## Feature

- [ ] Compare generated output with user edits; analyze the diffs to see which changes can be solved upstream in generation instead `[user]`
- [ ] Understand how local/destination data is created; explore tuning it to be more kid-friendly and less overly specific `[user]`
- [ ] Explore an automatic flow from doodle-style reference images to sorted local destination data `[user]`
- [ ] Validate and improve the quality of generated image prompts `[user]`
- [ ] Maze activity feels boring — explore ways to enrich the experience `[user]`
- [ ] Add a workbook-completion flow: a generated workbook isn't "done" until every page's art exists — track and show completion as a percentage / remaining-steps count, walk the user through each page's image prompt (`prompts/NN_<activity>.md` / `ImageBrief`) letting them choose per page between auto-generating the image (once `ImageBackend` is implemented) or uploading their own art, and mark the workbook complete once every page has art `[user]`
- [ ] Visual QA pass on the Hebrew/RTL layout (`HtmlRenderer` / PDF output) — only one non-English locale exists and RTL-specific rendering bugs are easy to miss without actually looking at output `[claude]`

## Bug

- [x] Word search words must not be editable/changeable after generation (data integrity between word list and grid) `[user]` — done 2026-08-13: `word_search.py`'s `_build_grid` generates the grid and word list together in one step, both stored in the same page metadata that the print layout typesets directly (`layouts.py:_word_search`). No CLI, web form, or renderer path lets words be edited independently of the grid, so there's no live mechanism for the two to drift apart.
- [ ] `src/uploads.py`'s hand-rolled multipart parser has no max body/file-size limit — a large upload to the web form could exhaust memory `[claude]`
