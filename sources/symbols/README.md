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
