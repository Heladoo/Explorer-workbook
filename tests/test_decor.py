"""Whether a destination already has a doodle sheet under sources/Decor/."""

from __future__ import annotations

from src.decor import existing_doodle


def test_no_decor_root_means_no_doodle(tmp_path):
    assert existing_doodle("Pelion", root=tmp_path / "does-not-exist") is None


def test_a_destination_with_no_directory_has_no_doodle(tmp_path):
    (tmp_path / "Prague").mkdir()
    assert existing_doodle("Pelion", root=tmp_path) is None


def test_a_directory_with_no_doodle_file_counts_as_none(tmp_path):
    (tmp_path / "Pelion").mkdir()
    (tmp_path / "Pelion" / "notes.txt").write_text("not a sheet")
    assert existing_doodle("Pelion", root=tmp_path) is None


def test_finds_a_doodle_by_slug_match(tmp_path):
    directory = tmp_path / "Pelion"
    directory.mkdir()
    sheet = directory / "doodle pelion.png"
    sheet.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert existing_doodle("Pelion", root=tmp_path) == sheet
    # Matched by slug, so case and spacing in either side don't matter.
    assert existing_doodle("pelion", root=tmp_path) == sheet


def test_ignores_files_that_are_not_doodle_sheets(tmp_path):
    directory = tmp_path / "Pelion"
    directory.mkdir()
    (directory / "map.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert existing_doodle("Pelion", root=tmp_path) is None
