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
- [ ] Figure out how many image generations are actually needed (scope/cost for the `ImageBackend` seam) `[user]`
- [ ] Delete all unused prompt files `[user]`
- [ ] Add CI (e.g. GitHub Actions) to run `pytest` automatically on push/PR — no workflow currently exists `[claude]`
- [ ] Add a dependency manifest (`pyproject.toml` / `requirements.txt`) pinning versions, including Playwright for `--pdf` — none exists today; overlaps with the release task above `[claude]`
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
- [ ] Visual QA pass on the Hebrew/RTL layout (`HtmlRenderer` / PDF output) — only one non-English locale exists and RTL-specific rendering bugs are easy to miss without actually looking at output `[claude]`

## Bug

- [ ] Word search words must not be editable/changeable after generation (data integrity between word list and grid) `[user]`
- [ ] `src/uploads.py`'s hand-rolled multipart parser has no max body/file-size limit — a large upload to the web form could exhaust memory `[claude]`
