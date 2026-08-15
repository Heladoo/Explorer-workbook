"""Smoke driver for the Explorer Workbook generator.

Drives both interaction surfaces in one run:

  1. CLI generation  (python -m src.cli)      — the surface most PRs touch:
     agents, activities, rendering all get exercised through here.
  2. HTML/PDF layout  (--html/--pdf)          — needs the checked-in
     Playwright/Chromium install; fails loudly if that's missing.
  3. Web form         (python -m src.web)     — smoke-checked over HTTP;
     for interactive UI poking, drive it with chromium-cli instead
     (see SKILL.md) since it's a real browser form.

Run from the repo root (the directory containing `src/`):

    python .claude/skills/run-explorer-workbook/driver.py

Exits non-zero on the first failed check.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kw)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"FAILED: {' '.join(cmd)} (exit {proc.returncode})")
    return proc


def check(label: str, condition: bool) -> None:
    status = "ok" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        raise SystemExit(f"FAILED check: {label}")


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="explorer_workbook_smoke_"))
    out_dir = tmp / "prague"
    print(f"== 1. CLI generation (json/md/prompts) -> {out_dir}")
    run(
        [
            sys.executable,
            "-m",
            "src.cli",
            "--destination",
            "Prague",
            "--children",
            "Noa,Amit",
            "--ages",
            "5,7",
            "--pages",
            "6",
            "--seed",
            "42",
            "--out",
            str(out_dir),
        ]
    )
    check("workbook.json written", (out_dir / "workbook.json").exists())
    check("workbook.md written", (out_dir / "workbook.md").exists())
    check("prompts/ has files", any((out_dir / "prompts").glob("*.md")))

    print("\n== 2. HTML + PDF layout (--pdf, needs playwright)")
    run(
        [
            sys.executable,
            "-m",
            "src.cli",
            "--destination",
            "Prague",
            "--children",
            "Noa,Amit",
            "--ages",
            "5,7",
            "--pages",
            "6",
            "--seed",
            "42",
            "--out",
            str(out_dir),
            "--pdf",
        ]
    )
    html = out_dir / "workbook.html"
    pdf = out_dir / "workbook.pdf"
    check("workbook.html written and non-trivial", html.exists() and html.stat().st_size > 10_000)
    check("workbook.pdf written and non-trivial", pdf.exists() and pdf.stat().st_size > 50_000)

    print("\n== 3. Web form smoke (python -m src.web)")
    proc = subprocess.Popen(
        [sys.executable, "-m", "src.web", "--port", "8091"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.time() + 10
        last_err = None
        while time.time() < deadline:
            try:
                resp = urllib.request.urlopen("http://127.0.0.1:8091/", timeout=1)
                check("GET / returns 200", resp.status == 200)
                body = resp.read().decode("utf-8", "replace")
                # cta_label is A/B-tested (src/experiments.py) so its text
                # varies per visitor cookie; check the stable form markup.
                check("form page has the submit button", 'type="submit"' in body)
                break
            except Exception as exc:  # noqa: BLE001 - retry until the server is up
                last_err = exc
                time.sleep(0.5)
        else:
            raise SystemExit(f"web server never came up: {last_err}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    print(f"\nAll checks passed. Sample artifacts left in: {out_dir}")
    print("(not auto-deleted — inspect workbook.pdf / workbook.html directly)")


if __name__ == "__main__":
    main()
