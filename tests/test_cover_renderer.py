from rich.text import Text

import cover_renderer
from cover_renderer import CoverRenderer


def test_render_returns_blank_when_cover_is_missing():
    renderer = CoverRenderer()

    assert renderer.render(None) == ""


def test_ansi_to_text_decodes_chafa_output():
    renderer = CoverRenderer()

    renderable = renderer._ansi_to_text("\x1b[31mcover\x1b[0m\n\x1b[34mart\x1b[0m")

    assert isinstance(renderable, Text)
    assert renderable.plain == "cover\nart"


def test_render_calls_chafa_cli_with_expected_options(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    renderer = CoverRenderer(width=36)
    called_command = []

    monkeypatch.setattr(cover_renderer.shutil, "which", lambda command: "/usr/bin/chafa")

    def fake_check_output(command, text, stderr):
        called_command.extend(command)
        return "\x1b[31mcover\x1b[0m\n"

    monkeypatch.setattr(cover_renderer.subprocess, "check_output", fake_check_output)

    renderable = renderer.render(str(cover))

    assert renderable.plain == "cover"
    assert called_command == [
        "/usr/bin/chafa",
        "--format=symbols",
        "--colors=full",
        "--dither=diffusion",
        "--preprocess=on",
        "--animate=off",
        "--label=off",
        "--relative=off",
        "--stretch",
        "--size=36x27",
        str(cover),
    ]


def test_rows_are_automatic_from_two_by_three_ratio_and_terminal_cell_shape():
    assert CoverRenderer(width=36).rows == 27
    assert CoverRenderer(width=48).rows == 36


def test_render_returns_unavailable_text_when_chafa_is_missing(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    renderer = CoverRenderer(width=2)

    monkeypatch.setattr(cover_renderer.shutil, "which", lambda command: None)

    renderable = renderer.render(str(cover))

    assert isinstance(renderable, Text)
    assert "chafa missing" in renderable.plain


def test_render_caches_by_path_mtime_and_size(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    renderer = CoverRenderer(width=2)

    monkeypatch.setattr(cover_renderer.shutil, "which", lambda command: "/usr/bin/chafa")
    monkeypatch.setattr(cover_renderer.subprocess, "check_output", lambda command, text, stderr: "cover")

    first = renderer.render(str(cover))
    second = renderer.render(str(cover))

    assert first is second
