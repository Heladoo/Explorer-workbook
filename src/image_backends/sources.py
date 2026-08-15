"""Pre-generates the reusable prompt files for the scavenger hunt's symbol bank.

A universal symbol's prompt names no destination, no characters and no house
style (see ``src/templates/symbol_prompt.tmpl``), so it renders identically no
matter which book asks for it. That means its prompt — and, once rendered, its
artwork — belongs to the whole repository rather than to any one generated
book. This module writes them once into ``sources/symbols/``, checked into the
repo so a fresh clone already has them, and which every run can then point
``--symbol-cache`` at to reuse whatever artwork has been dropped in alongside.

    python -m src.image_backends.sources
"""

from __future__ import annotations

from pathlib import Path

from src.activities._symbols import UNIVERSAL_SYMBOLS
from src.agents.prompt_generator import PromptGenerator
from src.models.context import WorkbookContext
from src.models.page import SymbolBrief

#: Repo root / sources / symbols — a sibling of src/, data/ and output/.
DEFAULT_SOURCES_DIR = Path(__file__).resolve().parents[2] / "sources" / "symbols"

_README = """\
# Scavenger hunt symbols

Prompts and artwork for the universal symbol bank in
`src/activities/_symbols.py` — the everyday things (a stop sign, a bridge, a
police car, ...) that make a scavenger hunt page finishable on any trip,
in any book, without depending on that destination's own knowledge pack.

## Why this lives outside `output/`

A universal symbol's prompt carries no destination, no recurring characters
and no house style, so the same prompt — and the same drawing — is correct in
every book that asks for it. `output/<destination>/` is one book's artifacts
and is otherwise disposable; this directory is the opposite: it is meant to
accumulate across every book ever generated, and to be committed.

## Layout

- `prompts/<key>.md` — one prompt per symbol, ready to paste into an image
  model. Regenerate with `python -m src.image_backends.sources`.
- `images/` — drop generated artwork here as `<key>.<ext>` (e.g.
  `stop-sign.png`). Point `--symbol-cache sources/symbols/images` at this
  directory and every book reuses whatever's already here instead of paying
  to regenerate it — see `generate_symbol_images()` in
  `src/image_backends/runner.py`.
- `cutouts/` and `silhouettes/` — derived from `images/` by
  `python tools/make_shadow_symbols.py`: the drawing with its ruled border
  removed and its paper cut away, and the same shape filled solid grey. The
  matching page ("Match the Shadows") places one of each per pair, both cut
  from a single crop box so a drawing and its shadow print at the same size.
  Regenerate after adding artwork to `images/`.

Every variant is looked up by `src/symbol_art.py` and picked up on any run
that lays the book out for print — `--generate-images` is only needed to
*create* artwork, never to use what is already here.
"""


def write_symbol_prompts(
    output_dir: Path | str = DEFAULT_SOURCES_DIR,
    *,
    generator: PromptGenerator | None = None,
) -> dict[str, Path]:
    """Render every universal symbol's prompt to ``<output_dir>/prompts/<key>.md``.

    Uses a bare, destination-less context: universal symbols carry no
    destination-specific wording, so the context default age band (a wide,
    reasonable middle) fits any book that might reuse them. Returns
    ``{symbol.key: path}``.
    """
    generator = generator or PromptGenerator()
    context = WorkbookContext(destination="")
    root = Path(output_dir)
    prompts_dir = root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (root / "images").mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for symbol in UNIVERSAL_SYMBOLS:
        brief = SymbolBrief(key=symbol.key, label=symbol.label, subject=symbol.subject)
        prompt = generator.render_symbol(brief, context)
        path = prompts_dir / f"{symbol.key}.md"
        path.write_text(generator.prompt_file(prompt), encoding="utf-8")
        written[symbol.key] = path
    return written


def write_readme(output_dir: Path | str = DEFAULT_SOURCES_DIR) -> Path:
    """Write the directory's explanatory ``README.md``, so a fresh clone
    (or a browsing human) knows what this folder is and how to use it."""
    path = Path(output_dir) / "README.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_README, encoding="utf-8")
    return path


if __name__ == "__main__":
    written = write_symbol_prompts()
    write_readme()
    print(f"Wrote {len(written)} symbol prompts to {DEFAULT_SOURCES_DIR / 'prompts'}")
