import hashlib
from pathlib import Path

from table_manager import TableManager


def test_table_paths_finds_vpx_files_recursively(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    table = nested / "table.vpx"
    ignored = nested / "readme.txt"
    table.write_text("vpx", encoding="utf-8")
    ignored.write_text("ignored", encoding="utf-8")
    manager = object.__new__(TableManager)
    manager.tables_root = str(tmp_path)

    assert manager._table_paths() == [str(table)]


def test_md5_matches_fixture_file():
    fixture = Path(__file__).parent / "fixtures" / "JP's Pokemon Pinball v4.3-horizontal.vpx"
    manager = object.__new__(TableManager)

    expected = hashlib.md5(fixture.read_bytes()).hexdigest()

    assert manager._md5(str(fixture)) == expected


def test_cover_path_finds_sibling_jpg(tmp_path):
    table = tmp_path / "table.vpx"
    cover = tmp_path / "cover.jpg"
    table.write_text("vpx", encoding="utf-8")
    cover.write_text("cover", encoding="utf-8")
    manager = object.__new__(TableManager)

    assert manager._cover_path(str(table)) == str(cover)


def test_cover_path_finds_sibling_jpeg(tmp_path):
    table = tmp_path / "table.vpx"
    cover = tmp_path / "cover.jpeg"
    table.write_text("vpx", encoding="utf-8")
    cover.write_text("cover", encoding="utf-8")
    manager = object.__new__(TableManager)

    assert manager._cover_path(str(table)) == str(cover)


def test_cover_path_finds_sibling_png(tmp_path):
    table = tmp_path / "table.vpx"
    cover = tmp_path / "cover.png"
    table.write_text("vpx", encoding="utf-8")
    cover.write_text("cover", encoding="utf-8")
    manager = object.__new__(TableManager)

    assert manager._cover_path(str(table)) == str(cover)


def test_cover_path_returns_none_when_missing(tmp_path):
    table = tmp_path / "table.vpx"
    table.write_text("vpx", encoding="utf-8")
    manager = object.__new__(TableManager)

    assert manager._cover_path(str(table)) is None
