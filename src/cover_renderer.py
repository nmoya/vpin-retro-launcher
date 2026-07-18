import logging
import os

from PIL import Image, ImageOps, UnidentifiedImageError
from rich.style import Style
from rich.text import Text

logger = logging.getLogger(__name__)

HALF_BLOCK = "▀"
COVER_ASPECT_WIDTH = 2
COVER_ASPECT_HEIGHT = 3


class CoverRenderer:
    def __init__(self, width: int = 48, max_rows: int = 36) -> None:
        self.width = width
        self.max_rows = max_rows
        self.cache: dict[tuple[str, float, int, int], Text] = {}

    def render(self, cover_path: str | None) -> Text | str:
        if not cover_path:
            return "[dim]No cover image[/]"

        try:
            mtime = os.path.getmtime(cover_path)
        except OSError as error:
            logger.warning("Unable to read cover image %s: %s", cover_path, error)
            return "[dim]Cover image unavailable[/]"

        key = (cover_path, mtime, self.width, self.max_rows)
        if key not in self.cache:
            self.cache[key] = self._render_uncached(cover_path)

        return self.cache[key]

    def _render_uncached(self, cover_path: str) -> Text:
        try:
            with Image.open(cover_path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image = ImageOps.fit(image, self._target_image_size(), Image.Resampling.LANCZOS)
                if image.height % 2:
                    image = self._pad_odd_height(image)
                return self._render_image(image)
        except (OSError, UnidentifiedImageError) as error:
            logger.warning("Unable to render cover image %s: %s", cover_path, error)
            return Text("Cover image unavailable", style="dim")

    def _render_image(self, image: Image.Image) -> Text:
        output = Text()
        pixels = image.load()

        for y in range(0, image.height, 2):
            for x in range(image.width):
                top = pixels[x, y]
                bottom = pixels[x, y + 1]
                output.append(HALF_BLOCK, style=self._style(top, bottom))

            if y + 2 < image.height:
                output.append("\n")

        return output

    def _pad_odd_height(self, image: Image.Image) -> Image.Image:
        padded = Image.new("RGB", (image.width, image.height + 1), (0, 0, 0))
        padded.paste(image, (0, 0))
        return padded

    def _target_image_size(self) -> tuple[int, int]:
        target_width = self.width
        target_height = round(target_width * COVER_ASPECT_HEIGHT / COVER_ASPECT_WIDTH)
        max_height = self.max_rows * 2

        if target_height > max_height:
            target_height = max_height
            target_width = round(target_height * COVER_ASPECT_WIDTH / COVER_ASPECT_HEIGHT)

        if target_height % 2:
            target_height += 1

        return (max(target_width, 1), max(target_height, 2))

    def _style(self, foreground: tuple[int, int, int], background: tuple[int, int, int]) -> Style:
        return Style(
            color=f"rgb({foreground[0]},{foreground[1]},{foreground[2]})",
            bgcolor=f"rgb({background[0]},{background[1]},{background[2]})",
        )
