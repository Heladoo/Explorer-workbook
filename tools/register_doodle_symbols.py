"""Turn approved doodle-sheet labels into real symbol library entries.

The last step of the doodle pipeline: ``split_decor.py`` cuts a doodle sheet
into numbered crops, a human (or an agent with vision, reviewing
``_contact.png``) proposes a key/label/subject/topic/ubiquity/roles for each
one worth keeping, and once that's approved this script:

1. copies each crop to ``sources/symbols/images/<key>.png``,
2. derives its cut-out and silhouette via ``tools/make_shadow_symbols.py``,
3. and — only for a genuinely new key — appends the entry to
   ``data/symbols/library.json``. A key that already exists in the library
   gets fresh artwork only; its entry is left alone (see the symbol-authoring
   skill's "easiest thing to forget" note about this step).

Unlike ``split_decor.py``/``make_shadow_symbols.py`` this *does* import from
``src`` — reusing the strict library loader (``src/symbols/loader.py``) and
``slugify`` (``src/models/context.py``) rather than re-implementing their
validation. Both are themselves stdlib-only, so this stays a plain authoring
tool; nothing under ``src/`` imports back from ``tools/``.

    python tools/register_doodle_symbols.py review.json
    python tools/register_doodle_symbols.py review.json --dry-run

``review.json``::

    {
      "entries": [
        {
          "crop": "sources/Decor/Pelion/split/doodle-pelion/symbol_003.png",
          "key": "olive-tree",
          "label": "an olive tree",
          "subject": "a gnarled olive tree with silvery leaves",
          "topic": "nature",
          "ubiquity": "regional",
          "status": "ready",
          "roles": ["spot"],
          "regions": ["greece", "mediterranean"]
        }
      ]
    }

Nothing is ever deleted, and an invalid entry aborts before anything is
written — the whole batch is validated against the real library schema
first, in memory, so a bad tag value never lands in the shared library file.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.models.context import slugify  # noqa: E402
from src.symbols.loader import LibraryError, load_library  # noqa: E402

LIBRARY_PATH = REPO_ROOT / "data" / "symbols" / "library.json"
IMAGES_DIR = REPO_ROOT / "sources" / "symbols" / "images"
MAKE_SHADOW_SCRIPT = Path(__file__).parent / "make_shadow_symbols.py"

_REQUIRED_FIELDS = ("key", "label", "subject", "topic", "ubiquity", "status")
_OPTIONAL_LIST_FIELDS = ("environments", "climate", "regions", "roles", "aliases")


def _load_review(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries", payload) if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise SystemExit(f"{path}: expected a list of entries (or {{'entries': [...]}})")
    return entries


def _validate(payload: dict) -> None:
    """Round-trip through the real strict loader before anything is written."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    ) as handle:
        json.dump(payload, handle)
        temp_path = Path(handle.name)
    try:
        load_library(temp_path)
    except LibraryError as exc:
        raise SystemExit(f"review produces an invalid library: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)


def register(review_path: Path, *, dry_run: bool, overwrite: bool) -> int:
    entries = _load_review(review_path)
    if not entries:
        print("nothing to register")
        return 0

    library_payload = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    existing_keys = {row["key"] for row in library_payload["symbols"]}

    new_rows: list[dict] = []
    copies: list[tuple[Path, Path]] = []

    for entry in entries:
        missing = [field for field in _REQUIRED_FIELDS if field not in entry]
        if missing:
            raise SystemExit(f"entry {entry.get('crop', entry)!r} missing field(s): {missing}")
        key = entry["key"]
        if slugify(key) != key:
            raise SystemExit(f"key {key!r} is not already a slug")
        crop = Path(entry["crop"])
        if not crop.is_file():
            raise SystemExit(f"crop not found: {crop}")

        target = IMAGES_DIR / f"{key}.png"
        if target.exists() and not overwrite:
            print(f"skip {key}: {target} already exists (pass --overwrite to replace)")
        else:
            copies.append((crop, target))

        if key in existing_keys:
            print(f"{key} is already in the library — refreshing artwork only, no new entry")
            continue

        row = {field: entry[field] for field in _REQUIRED_FIELDS}
        for field in _OPTIONAL_LIST_FIELDS:
            if field in entry:
                row[field] = entry[field]
        new_rows.append(row)
        existing_keys.add(key)

    updated_payload = {"symbols": [*library_payload["symbols"], *new_rows]}
    _validate(updated_payload)

    if dry_run:
        print(f"would copy {len(copies)} image(s), add {len(new_rows)} new library entry(ies)")
        for crop, target in copies:
            print(f"  {crop} -> {target}")
        for row in new_rows:
            print(f"  + {row['key']}: {row['label']}")
        return 0

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    for crop, target in copies:
        target.write_bytes(crop.read_bytes())

    if new_rows:
        LIBRARY_PATH.write_text(
            json.dumps(updated_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"added {len(new_rows)} new entry(ies) to {LIBRARY_PATH}")

    derive_keys = [target.stem for _, target in copies]
    if derive_keys:
        subprocess.run(
            [sys.executable, str(MAKE_SHADOW_SCRIPT), *derive_keys], check=True, cwd=REPO_ROOT
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("review", type=Path, help="approved review.json")
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    parser.add_argument("--overwrite", action="store_true", help="replace existing artwork")
    args = parser.parse_args(argv)
    return register(args.review, dry_run=args.dry_run, overwrite=args.overwrite)


if __name__ == "__main__":
    raise SystemExit(main())
