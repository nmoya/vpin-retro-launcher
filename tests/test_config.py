import json

import pytest

from config import Config


def write_config(tmp_path, data):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")
    return config_path


def test_valid_config_returns_properties(tmp_path):
    vpxtool = tmp_path / "vpxtool"
    vpinball = tmp_path / "vpinball"
    chafa = tmp_path / "chafa"
    tables_root = tmp_path / "tables"
    vpxtool.write_text("", encoding="utf-8")
    vpinball.write_text("", encoding="utf-8")
    chafa.write_text("", encoding="utf-8")
    tables_root.mkdir()
    config_path = write_config(
        tmp_path,
        {
            "orientation": "vertical",
            "vpxtool_path": str(vpxtool),
            "vpinball_path": str(vpinball),
            "chafa_path": str(chafa),
            "cover_art_width": 80,
            "tables_root": str(tables_root),
        },
    )

    config = Config(config_path)

    assert config.is_valid() is True
    assert config.orientation == "vertical"
    assert config.vpxtool_path == str(vpxtool)
    assert config.vpinball_path == str(vpinball)
    assert config.chafa_path == str(chafa)
    assert config.cover_art_width == 80
    assert config.tables_root == str(tables_root)


def test_missing_config_does_not_raise_during_initialization(tmp_path):
    config = Config(tmp_path / "missing.json")

    assert config.is_valid() is False


def test_invalid_orientation_raises_on_access(tmp_path):
    config_path = write_config(tmp_path, {"orientation": "diagonal"})
    config = Config(config_path)

    with pytest.raises(ValueError, match="Invalid orientation"):
        config.orientation


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("vpxtool_path", "/missing/vpxtool"),
        ("vpinball_path", "/missing/vpinball"),
        ("chafa_path", "/missing/chafa"),
        ("tables_root", "/missing/tables"),
        ("cover_art_width", "0"),
        ("cover_art_width", "not an int"),
    ],
)
def test_invalid_paths_make_config_invalid(tmp_path, field, value):
    data = {
        "orientation": "horizontal",
        "vpxtool_path": str(tmp_path / "vpxtool"),
        "vpinball_path": str(tmp_path / "vpinball"),
        "chafa_path": str(tmp_path / "chafa"),
        "cover_art_width": 72,
        "tables_root": str(tmp_path / "tables"),
    }
    (tmp_path / "vpxtool").write_text("", encoding="utf-8")
    (tmp_path / "vpinball").write_text("", encoding="utf-8")
    (tmp_path / "chafa").write_text("", encoding="utf-8")
    (tmp_path / "tables").mkdir()
    data[field] = value
    config = Config(write_config(tmp_path, data))

    assert config.is_valid() is False


def test_cover_art_width_defaults_to_72(tmp_path):
    vpxtool = tmp_path / "vpxtool"
    vpinball = tmp_path / "vpinball"
    chafa = tmp_path / "chafa"
    tables_root = tmp_path / "tables"
    vpxtool.write_text("", encoding="utf-8")
    vpinball.write_text("", encoding="utf-8")
    chafa.write_text("", encoding="utf-8")
    tables_root.mkdir()
    config_path = write_config(
        tmp_path,
        {
            "vpxtool_path": str(vpxtool),
            "vpinball_path": str(vpinball),
            "chafa_path": str(chafa),
            "tables_root": str(tables_root),
        },
    )

    assert Config(config_path).cover_art_width == 72
