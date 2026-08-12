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
