"""The public entry point.

    from src import generate_workbook

    result = generate_workbook(
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[5, 7],
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from src.agents.destination_agent import build_knowledge_agent
from src.output_writer import WrittenArtifacts, default_output_dir, write_bundle
from src.pipeline import WorkbookBuilder, WorkbookBundle, WorkbookRequest
from src.qa import LeakFinding, find_english_leaks


@dataclass(frozen=True)
class GenerationResult:
    """The generated workbook plus, when written, where it landed on disk."""

    bundle: WorkbookBundle
    artifacts: WrittenArtifacts | None = None
    #: Possible English leaked into a non-English workbook — see :mod:`src.qa`.
    #: Always empty for an English workbook.
    language_qa: tuple[LeakFinding, ...] = ()

    @property
    def workbook(self):
        return self.bundle.workbook

    @property
    def output_dir(self) -> Path | None:
        return self.artifacts.output_dir if self.artifacts else None


def generate_workbook(
    destination: str,
    children: Sequence[str] | None = None,
    ages: Sequence[int] | None = None,
    *,
    language: str = "en",
    page_count: int = 12,
    difficulty: str | None = None,
    theme: str | None = None,
    interests: Sequence[str] | None = None,
    itinerary: Sequence[str] | None = None,
    duration_days: int | None = None,
    start_date: str | None = None,
    family_photos: Sequence[str] | None = None,
    seed: int = 0,
    provider: str = "auto",
    data_dir: Path | str | None = None,
    output_dir: Path | str | None = None,
    output_root: Path | str | None = None,
    write: bool = True,
    html: bool = False,
    pdf: bool = False,
    ink_saver: bool = False,
    images: dict[int, Path] | None = None,
    symbol_images: dict[str, Path] | None = None,
    builder: WorkbookBuilder | None = None,
) -> GenerationResult:
    """Generate a workbook and, unless ``write=False``, write the three artifacts.

    ``provider`` chooses the knowledge chain: ``auto`` (curated packs, then the
    model), ``file``, ``llm`` or ``heuristic``. ``output_dir`` overrides the
    default ``output/<destination-slug>``.

    ``html`` and ``pdf`` additionally lay the workbook out for print; ``ink_saver``
    flattens that print layout's brand colors to grayscale. ``images`` maps page
    numbers to illustration files when artwork exists, and ``symbol_images`` maps
    a symbol slug to its drawing for pages laid out as a table of pictures.
    """
    request = WorkbookRequest(
        destination=destination,
        children=tuple(children or ()),
        ages=tuple(ages or ()),
        language=language,
        page_count=page_count,
        difficulty=difficulty,
        theme=theme,
        interests=tuple(interests or ()),
        itinerary=tuple(itinerary or ()),
        duration_days=duration_days,
        start_date=start_date,
        family_photos=tuple(family_photos or ()),
        seed=seed,
    )

    active_builder = builder or WorkbookBuilder(
        knowledge_agent=build_knowledge_agent(provider, data_dir=data_dir)
    )
    bundle = active_builder.build(request)
    language_qa = tuple(find_english_leaks(bundle.workbook, bundle.context))

    if not write:
        return GenerationResult(bundle=bundle, language_qa=language_qa)

    target = Path(output_dir) if output_dir else default_output_dir(
        bundle.context.slug if bundle.context else request.destination, output_root
    )
    return GenerationResult(
        bundle=bundle,
        artifacts=write_bundle(
            bundle,
            target,
            html=html,
            pdf=pdf,
            ink_saver=ink_saver,
            images=images,
            symbol_images=symbol_images,
        ),
        language_qa=language_qa,
    )
