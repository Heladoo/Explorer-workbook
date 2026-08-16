"""Command line interface.

    python -m src.cli --destination "Kfar Hanokdim" --children Noa,Amit --ages 5,7
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from src.agents.destination_agent import FileKnowledgeProvider
from src.api import generate_workbook
from src.image_backends.openrouter import DEFAULT_MODEL, OpenRouterImageBackend
from src.image_backends.runner import generate_images, generate_symbol_images
from src.image_backends.sources import DEFAULT_SOURCES_DIR, write_readme, write_symbol_prompts
from src.output_writer import write_bundle
from src.strings import available_languages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_workbook",
        description="Generate a printable children's travel activity workbook "
        "specification: workbook.json, workbook.md and one image prompt per page.",
    )
    parser.add_argument("--destination", "-d", help="Where the family is going.")
    parser.add_argument(
        "--children",
        default="",
        help="Comma-separated child names, e.g. 'Noa,Amit'.",
    )
    parser.add_argument(
        "--ages",
        default="",
        help="Comma-separated ages, in the same order as --children.",
    )
    parser.add_argument("--language", "-l", default="en", help="Workbook language (default: en).")
    parser.add_argument("--pages", "-p", type=int, default=12, help="How many pages (default: 12).")
    parser.add_argument(
        "--difficulty",
        choices=("easy", "medium", "hard"),
        help="Force one difficulty for every page instead of ramping.",
    )
    parser.add_argument("--theme", help="Optional theme, e.g. 'desert explorers'.")
    parser.add_argument(
        "--interests",
        default="",
        help="Comma-separated interests, e.g. 'animals,castles,trains'.",
    )
    parser.add_argument(
        "--itinerary",
        default="",
        help="Comma-separated itinerary entries, one per day.",
    )
    parser.add_argument("--duration-days", type=int, help="Trip length in days.")
    parser.add_argument("--start-date", help="Trip start date, free text or ISO.")
    parser.add_argument(
        "--photo",
        action="append",
        default=[],
        dest="photos",
        help="Path to a family photo. Recorded in metadata; not placed by the MVP.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Seed for reproducible output.")
    parser.add_argument(
        "--provider",
        default="auto",
        choices=("auto", "file", "llm", "heuristic"),
        help="Knowledge source chain (default: auto — curated packs, then the model).",
    )
    parser.add_argument("--data-dir", help="Directory of curated destination packs.")
    parser.add_argument("--out", help="Output directory (default: output/<destination-slug>).")
    parser.add_argument(
        "--html",
        action="store_true",
        help="Also lay the workbook out as a printable A4 HTML document.",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also print the workbook to A4 PDF (implies --html; needs playwright).",
    )
    parser.add_argument(
        "--ink-saver",
        action="store_true",
        help="Flatten the print layout's brand colors to grayscale, for cheap "
        "home printing.",
    )
    parser.add_argument(
        "--list-destinations",
        action="store_true",
        help="List destinations that have a curated data pack, then exit.",
    )
    parser.add_argument(
        "--generate-images",
        action="store_true",
        help="Render every page's image_prompt via OpenRouter (needs OPENROUTER_API_KEY).",
    )
    parser.add_argument(
        "--image-model",
        default=DEFAULT_MODEL,
        help=f"OpenRouter model slug for image generation (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--symbol-cache",
        default=str(DEFAULT_SOURCES_DIR / "images"),
        help="Directory of reusable scavenger-hunt symbol drawings, reused across "
        "every book and shared with the repo's pre-generated set "
        f"(default: {DEFAULT_SOURCES_DIR / 'images'}).",
    )
    parser.add_argument(
        "--write-symbol-sources",
        action="store_true",
        help=f"Write every universal scavenger-hunt symbol's prompt to "
        f"{DEFAULT_SOURCES_DIR}/prompts/ (checked into the repo, reused by every "
        "book — see sources/symbols/README.md), then exit.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Show provider decisions.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.list_destinations:
        known = FileKnowledgeProvider(args.data_dir).known_destinations()
        print("Curated destination packs:")
        for name in known or ("(none found)",):
            print(f"  - {name}")
        print("\nAny other destination works too, via --provider llm or generic material.")
        return 0

    if args.write_symbol_sources:
        written = write_symbol_prompts()
        write_readme()
        print(f"Wrote {len(written)} symbol prompts to {DEFAULT_SOURCES_DIR / 'prompts'}")
        return 0

    if not args.destination:
        build_parser().error("--destination is required (or use --list-destinations)")

    ages = _split_ints(args.ages, "--ages")
    children = _split(args.children)
    if ages and len(ages) != len(children):
        build_parser().error(
            f"--ages has {len(ages)} value(s) but --children has {len(children)}"
        )

    try:
        result = generate_workbook(
            destination=args.destination,
            children=children,
            ages=ages,
            language=args.language,
            page_count=args.pages,
            difficulty=args.difficulty,
            theme=args.theme,
            interests=_split(args.interests),
            itinerary=_split(args.itinerary),
            duration_days=args.duration_days,
            start_date=args.start_date,
            family_photos=args.photos,
            seed=args.seed,
            provider=args.provider,
            data_dir=args.data_dir,
            output_dir=args.out,
            html=args.html,
            pdf=args.pdf,
            ink_saver=args.ink_saver,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    workbook = result.workbook
    artifacts = result.artifacts
    assert artifacts is not None  # generate_workbook wrote by default

    if args.generate_images:
        backend = OpenRouterImageBackend(model=args.image_model)
        images_dir = artifacts.output_dir / "images"
        symbols_dir = Path(args.symbol_cache)
        context = result.bundle.context
        images = generate_images(workbook, context, backend, output_dir=images_dir)
        symbol_images = generate_symbol_images(
            workbook, context, backend, output_dir=symbols_dir
        )
        if images or symbol_images:
            artifacts = write_bundle(
                result.bundle,
                artifacts.output_dir,
                html=args.html,
                pdf=args.pdf,
                ink_saver=args.ink_saver,
                images=images,
                symbol_images=symbol_images,
            )
        print(f"  images      : {len(images)}/{workbook.page_count} pages")
        if symbol_images:
            print(f"  symbols     : {len(symbol_images)} in {symbols_dir}")

    print(f"{workbook.title}")
    print(f"  destination : {workbook.destination}")
    print(f"  language    : {workbook.language}")
    print(f"  knowledge   : {workbook.metadata.get('knowledge_source')}")
    print(f"  pages       : {workbook.page_count}")
    for page in workbook.pages:
        print(f"    {page.number:>2}. {page.type:<16} {page.title}")
    print(f"  written to  : {artifacts.output_dir}")
    written = [
        artifacts.workbook_json.name,
        artifacts.workbook_md.name,
        f"prompts/ ({len(artifacts.prompt_files)} files)",
    ]
    if artifacts.workbook_html:
        written.append(artifacts.workbook_html.name)
    if artifacts.workbook_pdf:
        written.append(artifacts.workbook_pdf.name)
    print(f"    {', '.join(written)}")
    if workbook.metadata.get("language_fallback"):
        print(f"  note        : {workbook.metadata['language_fallback']}")
        print(f"                available: {', '.join(available_languages())}")
    if result.language_qa:
        print(f"  language QA : {len(result.language_qa)} possible English leak(s)")
        for finding in result.language_qa:
            print(f"    - {finding}")
    return 0


def _split(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _split_ints(value: str, flag: str) -> tuple[int, ...]:
    parts = _split(value)
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise SystemExit(f"error: {flag} must be whole numbers, got {value!r}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
