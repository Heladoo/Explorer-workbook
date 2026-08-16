"""Smoke driver for the symbol-authoring pipeline (tools/split_decor.py +
tools/make_shadow_symbols.py).

Exercises both authoring tools against real checked-in inputs, writing only
to a scratch temp directory — never to sources/symbols/ itself:

  1. split_decor.py   — splits a multi-object doodle/grid sheet into one
                         crop per object (+ a contact sheet + manifest.json).
  2. make_shadow_symbols.py — derives a cutout (transparent, frame-stripped)
                         and a silhouette (solid-grey shadow) from a couple
                         of the checked-in sources/symbols/images/*.png.

Run from the repo root (the directory containing `src/`):

    python .claude/skills/symbol-authoring/driver.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    print(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(f"FAILED: {' '.join(cmd)} (exit {proc.returncode})")
    return proc


def check(label: str, condition: bool) -> None:
    status = "ok" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        raise SystemExit(f"FAILED check: {label}")


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="symbol_authoring_smoke_"))

    print("== 1. split_decor.py — split a real doodle sheet")
    sheet = REPO_ROOT / "sources" / "Decor" / "Pelion" / "doodle pelion.png"
    check("sample sheet exists", sheet.exists())
    split_out = tmp / "split"
    run([sys.executable, "tools/split_decor.py", str(sheet), "-o", str(split_out)])
    crop_dir = split_out / "doodle-pelion"
    crops = list(crop_dir.glob("symbol_*.png"))
    check("crops were written", len(crops) > 0)
    check("contact sheet written", (crop_dir / "_contact.png").exists())
    check("manifest.json written", (crop_dir / "manifest.json").exists())

    print("\n== 2. make_shadow_symbols.py — derive cutout + silhouette")
    cutouts = tmp / "cutouts"
    silhouettes = tmp / "silhouettes"
    run(
        [
            sys.executable,
            "tools/make_shadow_symbols.py",
            "bicycle",
            "dog",
            "--cutouts",
            str(cutouts),
            "--silhouettes",
            str(silhouettes),
        ]
    )
    check("cutouts/bicycle.png written", (cutouts / "bicycle.png").exists())
    check("cutouts/dog.png written", (cutouts / "dog.png").exists())
    check("silhouettes/bicycle.png written", (silhouettes / "bicycle.png").exists())
    check("silhouettes/dog.png written", (silhouettes / "dog.png").exists())
    check("cutout contact sheet written", (cutouts / "_contact.png").exists())
    check("silhouette contact sheet written", (silhouettes / "_contact.png").exists())

    print(f"\nAll checks passed. Scratch output left in: {tmp}")
    print("(nothing under sources/symbols/ was touched by this driver)")


if __name__ == "__main__":
    main()
