"""End-to-end: the success criteria from the brief, plus the output contracts."""

from __future__ import annotations

import json

import pytest

from src import generate_workbook
from src.agents.destination_agent import build_knowledge_agent
from src.cli import main
from src.pipeline import SCHEMA_VERSION, WorkbookBuilder, WorkbookRequest

from tests.conftest import DATA_DIR


def _generate(tmp_path, builder, **kwargs):
    return generate_workbook(
        output_dir=tmp_path / "book", builder=builder, **kwargs
    )


def test_success_criteria_produces_the_three_artifacts(tmp_path, builder):
    result = _generate(
        tmp_path,
        builder,
        destination="Kfar Hanokdim",
        children=["Noa", "Amit"],
        ages=[5, 7],
    )
    artifacts = result.artifacts

    assert artifacts.workbook_json.exists()
    assert artifacts.workbook_md.exists()
    # Only cover and coloring pages get their own prompt file — every other
    # page carries no illustration of its own (see src/pipeline.py) — plus
    # one shared doodle/grid sheet per book.
    illustrated = [page for page in result.workbook.pages if page.image_brief is not None]
    assert illustrated
    for page in illustrated:
        assert (artifacts.output_dir / "prompts" / page.prompt_filename).exists()
    for page in result.workbook.pages:
        if page.image_brief is None:
            assert not (artifacts.output_dir / "prompts" / page.prompt_filename).exists()
    assert (artifacts.output_dir / "prompts" / "doodle_grid.md").exists()


def test_no_doodle_grid_prompt_once_the_destination_already_has_a_sheet(
    tmp_path, builder, monkeypatch
):
    """A destination's doodle sheet is a one-time, hand-reviewed source for
    its symbols (see src/decor.py) — once it exists, books stop re-asking."""
    from src import decor

    decor_dir = tmp_path / "decor" / "Kfar Hanokdim"
    decor_dir.mkdir(parents=True)
    (decor_dir / "doodle kfar-hanokdim.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(decor, "DEFAULT_DECOR_ROOT", tmp_path / "decor")

    result = _generate(tmp_path, builder, destination="Kfar Hanokdim")
    assert "doodle_grid.md" not in result.bundle.prompts
    assert not (result.artifacts.output_dir / "prompts" / "doodle_grid.md").exists()


def test_workbook_json_has_the_documented_shape(tmp_path, builder):
    result = _generate(tmp_path, builder, destination="Kfar Hanokdim", children=["Noa"], ages=[5])
    data = json.loads(result.artifacts.workbook_json.read_text(encoding="utf-8"))

    assert data["destination"] == "Kfar Hanokdim"
    assert data["metadata"]["schema_version"] == SCHEMA_VERSION
    assert data["metadata"]["knowledge_source"] == "file"
    # Kfar Hanokdim has no itinerary, so no route map and therefore no centre
    # spread: every page is one slot and the two counts coincide. A book with
    # a spread is covered in test_booklet.py, where they deliberately don't.
    assert data["page_count"] == len(data["pages"])
    assert all(page.get("span", 1) == 1 for page in data["pages"])

    for index, page in enumerate(data["pages"], start=1):
        assert page["number"] == index
        for field in ("type", "title", "instructions", "educational_goal", "estimated_age", "prompt_file"):
            assert page[field], f"page {index} has an empty {field}"
        assert page["prompt_file"] == f"prompts/{index:02d}_{page['type']}.md"
        # Only cover/coloring pages carry an illustration brief and prompt —
        # every other type is text/puzzle-only now (see src/pipeline.py).
        if page["metadata"].get("image_brief"):
            assert page["image_prompt"]
            assert page["metadata"]["image_brief"]["render_mode"]
        else:
            assert page["image_prompt"] == ""


def test_prompt_files_match_the_prompts_in_the_json(tmp_path, builder):
    result = _generate(tmp_path, builder, destination="Prague", children=["Noa"], ages=[6])
    for page in result.workbook.pages:
        if page.image_brief is None:
            continue
        path = result.artifacts.output_dir / "prompts" / page.prompt_filename
        assert path.read_text(encoding="utf-8").strip() == page.image_prompt.strip()


def test_markdown_documents_every_required_field(tmp_path, builder):
    result = _generate(
        tmp_path, builder, destination="Kfar Hanokdim", children=["Noa", "Amit"], ages=[5, 7]
    )
    markdown = result.artifacts.workbook_md.read_text(encoding="utf-8")

    assert result.workbook.title in markdown
    for page in result.workbook.pages:
        assert f"### Page {page.number} — {page.title}" in markdown
        assert page.educational_goal in markdown
        assert page.instructions.splitlines()[0] in markdown
        if page.image_brief is not None:
            assert f"prompts/{page.prompt_filename}" in markdown
        assert page.estimated_age in markdown
    assert "Destination knowledge used" in markdown
    assert "$" not in markdown, "an unsubstituted template placeholder leaked through"


def test_same_inputs_produce_byte_identical_output(tmp_path):
    def run(target):
        return generate_workbook(
            destination="Kfar Hanokdim",
            children=["Noa", "Amit"],
            ages=[5, 7],
            output_dir=target,
            builder=WorkbookBuilder(
                knowledge_agent=build_knowledge_agent("file", data_dir=DATA_DIR),
                clock=lambda: "2026-01-01T00:00:00+00:00",
            ),
        )

    first = run(tmp_path / "a")
    second = run(tmp_path / "b")
    assert first.bundle.json == second.bundle.json
    assert first.bundle.markdown == second.bundle.markdown
    assert first.bundle.prompts == second.bundle.prompts


def test_a_different_seed_changes_the_content(tmp_path, builder):
    base = _generate(tmp_path, builder, destination="Kfar Hanokdim", write=False)
    varied = generate_workbook(
        destination="Kfar Hanokdim", seed=99, write=False, builder=builder
    )
    assert base.bundle.json != varied.bundle.json


def test_a_different_destination_produces_different_content(builder):
    desert = generate_workbook(destination="Kfar Hanokdim", write=False, builder=builder)
    city = generate_workbook(destination="Prague", write=False, builder=builder)

    assert desert.workbook.title != city.workbook.title
    desert_text = desert.bundle.json
    city_text = city.bundle.json
    assert "camel" in desert_text.lower()
    assert "camel" not in city_text.lower()
    prague_landmarks = (
        "Charles Bridge",
        "Prague Castle",
        "the Astronomical Clock",
        "Old Town Square",
        "Petrin Tower",
        "the Vltava river",
    )
    assert any(landmark in city_text for landmark in prague_landmarks)


def test_an_unknown_destination_still_produces_a_workbook(builder):
    result = generate_workbook(destination="Tbilisi", write=False, builder=builder)
    assert result.workbook.page_count >= 3
    assert result.workbook.metadata["knowledge_source"] == "heuristic"
    assert "generic travel material" in result.bundle.markdown


def test_children_are_optional(builder):
    result = generate_workbook(destination="Prague", write=False, builder=builder)
    assert "Prague" in result.workbook.title
    cover = result.workbook.page_by_type("cover")
    assert cover.metadata["personalized"] is False


def test_ages_must_line_up_with_children(builder):
    with pytest.raises(ValueError, match="one age per child"):
        generate_workbook(
            destination="Prague", children=["Noa"], ages=[5, 7], write=False, builder=builder
        )


def test_destination_is_required(builder):
    with pytest.raises(ValueError, match="destination is required"):
        generate_workbook(destination="  ", write=False, builder=builder)


def test_interests_and_itinerary_reach_the_output(builder):
    result = generate_workbook(
        destination="Prague",
        children=["Noa"],
        ages=[7],
        interests=["castles"],
        itinerary=["Old Town day", "Castle day"],
        write=False,
        builder=builder,
    )
    plan = result.workbook.metadata["plan"]
    assert {slot["itinerary_day"] for slot in plan} >= {"Old Town day", "Castle day"}
    assert result.workbook.metadata["request"]["interests"] == ["castles"]


def test_family_photos_are_recorded_but_not_placed(builder):
    result = generate_workbook(
        destination="Prague", family_photos=["/photos/beach.jpg"], write=False, builder=builder
    )
    assert result.workbook.metadata["family_photos"] == ["/photos/beach.jpg"]
    assert "does not place images" in result.bundle.markdown


def test_unavailable_language_falls_back_and_says_so(builder):
    result = generate_workbook(
        destination="Prague", language="fr", write=False, builder=builder
    )
    assert result.workbook.language == "en"
    assert result.workbook.metadata["requested_language"] == "fr"
    assert "fr is not available" in result.workbook.metadata["language_fallback"]
    assert "requested `fr`" in result.bundle.markdown


def test_page_count_is_respected_end_to_end(builder):
    result = generate_workbook(
        destination="Kfar Hanokdim", page_count=20, write=False, builder=builder
    )
    assert result.workbook.page_count == 20
    illustrated = [page for page in result.workbook.pages if page.image_brief is not None]
    page_prompts = [name for name in result.bundle.prompts if name != "doodle_grid.md"]
    assert len(page_prompts) == len(illustrated)


def test_request_builds_children_from_names_and_ages():
    context = WorkbookRequest(
        destination="Prague", children=("Noa", "Amit"), ages=(5,)
    ).to_context()
    assert context.children[0].age == 5
    assert context.children[1].age is None


def test_writing_twice_overwrites_cleanly(tmp_path, builder):
    first = _generate(tmp_path, builder, destination="Prague", page_count=12)
    second = _generate(tmp_path, builder, destination="Prague", page_count=12)
    assert first.artifacts.output_dir == second.artifacts.output_dir
    assert second.artifacts.workbook_json.read_text(encoding="utf-8") == second.bundle.json


# -- CLI ----------------------------------------------------------------


def test_cli_writes_the_artifacts(tmp_path, capsys):
    exit_code = main(
        [
            "--destination", "Kfar Hanokdim",
            "--children", "Noa,Amit",
            "--ages", "5,7",
            "--pages", "8",
            "--data-dir", str(DATA_DIR),
            "--provider", "file",
            "--out", str(tmp_path / "cli"),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert (tmp_path / "cli" / "workbook.json").exists()
    data = json.loads((tmp_path / "cli" / "workbook.json").read_text(encoding="utf-8"))
    illustrated = sum(1 for page in data["pages"] if page["metadata"].get("image_brief"))
    # One prompt file per illustrated page, plus the shared doodle/grid sheet.
    assert len(list((tmp_path / "cli" / "prompts").glob("*.md"))) == illustrated + 1
    assert "Kfar Hanokdim" in output


def test_cli_rejects_mismatched_ages(tmp_path):
    with pytest.raises(SystemExit):
        main(["--destination", "Prague", "--children", "Noa", "--ages", "5,7"])


def test_cli_lists_curated_destinations(capsys):
    assert main(["--list-destinations", "--data-dir", str(DATA_DIR)]) == 0
    assert "Kfar Hanokdim" in capsys.readouterr().out
