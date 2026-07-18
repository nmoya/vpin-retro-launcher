import subprocess

from rich.text import Text

import cover_renderer
from cover_renderer import CoverRenderer


def test_render_returns_blank_when_cover_is_missing(tmp_path):
    renderer = CoverRenderer("chafa", cache_dir=str(tmp_path / "cache"))

    assert renderer.render(None) == ""


def test_ansi_to_text_decodes_chafa_output(tmp_path):
    renderer = CoverRenderer("chafa", cache_dir=str(tmp_path / "cache"))

    renderable = renderer._ansi_to_text("\x1b[31mcover\x1b[0m\n\x1b[34mart\x1b[0m")

    assert isinstance(renderable, Text)
    assert renderable.plain == "cover\nart"


def test_render_calls_configured_chafa_and_writes_disk_cache(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    renderer = CoverRenderer("/usr/bin/chafa", width=36, cache_dir=str(tmp_path / "cache"))
    called_command = []

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
    assert len(list((tmp_path / "cache").glob("*.ansi"))) == 1


def test_render_reads_disk_cache_without_calling_chafa(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    cache_dir = tmp_path / "cache"
    first_renderer = CoverRenderer("/usr/bin/chafa", width=36, cache_dir=str(cache_dir))
    monkeypatch.setattr(
        cover_renderer.subprocess,
        "check_output",
        lambda command, text, stderr: "\x1b[31mcover\x1b[0m",
    )
    first_renderer.render(str(cover))

    def fail_if_called(command, text, stderr):
        raise AssertionError("chafa should not be called when disk cache exists")

    monkeypatch.setattr(cover_renderer.subprocess, "check_output", fail_if_called)
    second_renderer = CoverRenderer("/usr/bin/chafa", width=36, cache_dir=str(cache_dir))

    assert second_renderer.render(str(cover)).plain == "cover"


def test_cache_key_changes_when_width_changes(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(cover_renderer.subprocess, "check_output", lambda command, text, stderr: "cover")

    CoverRenderer("/usr/bin/chafa", width=36, cache_dir=str(cache_dir)).render(str(cover))
    CoverRenderer("/usr/bin/chafa", width=48, cache_dir=str(cache_dir)).render(str(cover))

    assert len(list(cache_dir.glob("*.ansi"))) == 2


def test_precache_writes_disk_cache_without_decoding(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    cache_dir = tmp_path / "cache"
    renderer = CoverRenderer("/usr/bin/chafa", width=36, cache_dir=str(cache_dir))
    monkeypatch.setattr(cover_renderer.subprocess, "check_output", lambda command, text, stderr: "cover")

    renderer.precache(str(cover))

    assert len(list(cache_dir.glob("*.ansi"))) == 1


def test_render_returns_unavailable_text_when_chafa_is_missing(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    renderer = CoverRenderer("/missing/chafa", width=2, cache_dir=str(tmp_path / "cache"))

    def raise_missing(command, text, stderr):
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(cover_renderer.subprocess, "check_output", raise_missing)

    renderable = renderer.render(str(cover))

    assert isinstance(renderable, Text)
    assert "Cover image unavailable" in renderable.plain
    assert not (tmp_path / "cache").exists()


def test_chafa_failure_does_not_write_disk_cache(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    renderer = CoverRenderer("/usr/bin/chafa", width=2, cache_dir=str(tmp_path / "cache"))

    def raise_error(command, text, stderr):
        raise subprocess.CalledProcessError(1, command, stderr="bad image")

    monkeypatch.setattr(cover_renderer.subprocess, "check_output", raise_error)

    renderable = renderer.render(str(cover))

    assert isinstance(renderable, Text)
    assert "Cover image unavailable" in renderable.plain
    assert not (tmp_path / "cache").exists()


def test_render_caches_in_memory(tmp_path, monkeypatch):
    cover = tmp_path / "cover.jpg"
    cover.write_bytes(b"image")
    renderer = CoverRenderer("/usr/bin/chafa", width=2, cache_dir=str(tmp_path / "cache"))
    monkeypatch.setattr(cover_renderer.subprocess, "check_output", lambda command, text, stderr: "cover")

    first = renderer.render(str(cover))
    second = renderer.render(str(cover))

    assert first is second
