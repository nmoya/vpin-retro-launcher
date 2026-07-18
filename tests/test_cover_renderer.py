from PIL import Image
from rich.text import Text

from cover_renderer import CoverRenderer, HALF_BLOCK


def test_render_returns_fallback_when_cover_is_missing():
    renderer = CoverRenderer()

    assert renderer.render(None) == "[dim]No cover image[/]"


def test_render_returns_half_block_text_for_image(tmp_path):
    cover = tmp_path / "cover.jpeg"
    image = Image.new("RGB", (4, 4), (255, 0, 0))
    image.putpixel((0, 1), (0, 0, 255))
    image.save(cover)
    renderer = CoverRenderer(width=4, max_rows=3)

    renderable = renderer.render(str(cover))

    assert isinstance(renderable, Text)
    assert HALF_BLOCK in renderable.plain
    assert len(renderable.plain.splitlines()) == 3


def test_render_uses_portrait_cover_aspect_ratio(tmp_path):
    cover = tmp_path / "cover.jpg"
    Image.new("RGB", (10, 10), (255, 0, 0)).save(cover)
    renderer = CoverRenderer(width=8, max_rows=6)

    renderable = renderer.render(str(cover))
    lines = renderable.plain.splitlines()

    assert len(lines) == 6
    assert all(len(line) == 8 for line in lines)


def test_render_pads_odd_height_images(tmp_path):
    cover = tmp_path / "cover.jpg"
    Image.new("RGB", (3, 3), (0, 255, 0)).save(cover)
    renderer = CoverRenderer(width=3, max_rows=4)

    renderable = renderer.render(str(cover))

    assert isinstance(renderable, Text)
    assert renderable.plain


def test_render_caches_by_path_mtime_and_size(tmp_path):
    cover = tmp_path / "cover.jpg"
    Image.new("RGB", (2, 2), (255, 255, 255)).save(cover)
    renderer = CoverRenderer(width=2, max_rows=1)

    first = renderer.render(str(cover))
    second = renderer.render(str(cover))

    assert first is second
