import json
import subprocess

from vpxtool_bridge import VPXToolBridge


def test_parse_info_output_maps_json_fields(tmp_path):
    info_path = tmp_path / "table.info.json"
    info_path.write_text(
        json.dumps(
            {
                "table_name": " Attack From Mars ",
                "vpx_version": "10.8",
                "table_version": "1.0",
                "table_save_date": "Oct 6, 2026",
                "table_description": "A table",
                "table_save_rev": "42",
            }
        ),
        encoding="utf-8",
    )

    info = VPXToolBridge("vpxtool")._parse_info_output("table.vpx", str(info_path))

    assert info.name == "Attack From Mars"
    assert info.vpx_version == "10.8"
    assert info.version == "1.0"
    assert info.published_date == "Oct 6, 2026"
    assert info.description == "A table"
    assert info.revision == "42"
    assert info.path == "table.vpx"


def test_parse_info_output_logs_missing_table_name(tmp_path, caplog):
    info_path = tmp_path / "table.info.json"
    info_path.write_text(json.dumps({"table_name": ""}), encoding="utf-8")

    info = VPXToolBridge("vpxtool")._parse_info_output("table.vpx", str(info_path))

    assert info.name == ""
    assert "Missing table name" in caplog.text


def test_scores_parses_vpxtool_output(monkeypatch):
    bridge = VPXToolBridge("vpxtool")
    monkeypatch.setattr(
        bridge,
        "execute",
        lambda args: "Name  Initials  Score\nPlayer One  PO  1,000\nMalformed\nPlayer Two  PT  2,000\n",
    )

    scores = bridge.scores("table.vpx")

    assert [(score.name, score.initials, score.score) for score in scores] == [
        ("Player One", "PO", "1,000"),
        ("Player Two", "PT", "2,000"),
    ]


def test_scores_returns_empty_on_vpxtool_error(monkeypatch, caplog):
    bridge = VPXToolBridge("vpxtool")

    def raise_error(args):
        raise subprocess.CalledProcessError(1, args, stderr="no high scores")

    monkeypatch.setattr(bridge, "execute", raise_error)

    assert bridge.scores("table.vpx") == []
    assert "Missing high scores" in caplog.text
