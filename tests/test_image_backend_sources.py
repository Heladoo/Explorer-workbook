"""Pre-generated symbol prompt sources: ``src/image_backends/sources.py``.

The universal symbol bank's prompts are destination-independent, so they are
generated once into ``sources/symbols/`` and checked into the repo rather than
regenerated per book — these tests pin that they're complete, stable, and
reusable as the ``--symbol-cache`` a real run would point at.
"""

from __future__ import annotations

from src.activities._symbols import UNIVERSAL_SYMBOLS
from src.image_backends.sources import write_readme, write_symbol_prompts


def test_writes_one_prompt_per_universal_symbol(tmp_path):
    written = write_symbol_prompts(tmp_path)

    assert set(written) == {symbol.key for symbol in UNIVERSAL_SYMBOLS}
    for key, path in written.items():
        assert path == tmp_path / "prompts" / f"{key}.md"
        assert path.is_file()


def test_a_written_prompt_matches_what_the_pipeline_would_generate(tmp_path):
    """The sources folder must not drift from what a real book produces —
    otherwise a cached drawing stops matching the prompt a fresh run asks for."""
    from src.agents.prompt_generator import PromptGenerator
    from src.models.context import WorkbookContext
    from src.models.page import SymbolBrief

    written = write_symbol_prompts(tmp_path)
    generator = PromptGenerator()
    context = WorkbookContext(destination="")

    symbol = UNIVERSAL_SYMBOLS[0]
    expected = generator.prompt_file(
        generator.render_symbol(
            SymbolBrief(key=symbol.key, label=symbol.label, subject=symbol.subject), context
        )
    )
    assert written[symbol.key].read_text(encoding="utf-8") == expected


def test_every_prompt_asks_for_one_subject_and_no_page_furniture(tmp_path):
    written = write_symbol_prompts(tmp_path)
    for symbol in UNIVERSAL_SYMBOLS:
        text = written[symbol.key].read_text(encoding="utf-8")
        assert symbol.subject in text
        assert "no checkbox" in text
        assert "destination" not in text.lower()


def test_symbol_prompt_keys_stay_stable_across_runs(tmp_path):
    """Regenerating must be idempotent — the whole point is a shared cache
    keyed by these slugs."""
    first = write_symbol_prompts(tmp_path)
    second = write_symbol_prompts(tmp_path)
    assert first.keys() == second.keys()
    for key in first:
        assert first[key].read_text(encoding="utf-8") == second[key].read_text(encoding="utf-8")


def test_write_symbol_prompts_creates_a_sibling_images_directory(tmp_path):
    """The runner's ``--symbol-cache`` reuse looks for ``<key>.*`` files inside
    whatever directory it's pointed at; ``images/`` is where those belong."""
    write_symbol_prompts(tmp_path)
    assert (tmp_path / "images").is_dir()


def test_write_readme_explains_the_layout(tmp_path):
    path = write_readme(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "prompts/" in text and "images/" in text


def test_the_committed_sources_directory_is_up_to_date():
    """A repo checkout should never need ``--write-symbol-sources`` run just to
    match the current symbol bank — catches a symbol added to ``_symbols.py``
    without regenerating ``sources/symbols/``."""
    from src.image_backends.sources import DEFAULT_SOURCES_DIR

    if not DEFAULT_SOURCES_DIR.is_dir():
        return  # nothing committed yet in this checkout; not this test's job to create it

    committed = {path.stem for path in (DEFAULT_SOURCES_DIR / "prompts").glob("*.md")}
    assert committed == {symbol.key for symbol in UNIVERSAL_SYMBOLS}
