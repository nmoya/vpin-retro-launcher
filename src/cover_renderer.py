import logging
import os
import shutil
import subprocess

from rich.ansi import AnsiDecoder
from rich.text import Text

logger = logging.getLogger(__name__)

COVER_ASPECT_WIDTH = 2
COVER_ASPECT_HEIGHT = 3
TERMINAL_CELL_WIDTH_TO_HEIGHT = 0.5


class CoverRenderer:
    def __init__(self, width: int = 72) -> None:
        self.width = width
        self.cache: dict[tuple[str, float, int, int], Text] = {}

    @property
    def rows(self) -> int:
        visual_ratio = COVER_ASPECT_HEIGHT / COVER_ASPECT_WIDTH
        return max(round(self.width * visual_ratio * TERMINAL_CELL_WIDTH_TO_HEIGHT), 1)

    def render(self, cover_path: str | None) -> Text | str:
        if not cover_path:
            return ""

        try:
            mtime = os.path.getmtime(cover_path)
        except OSError as error:
            logger.warning("Unable to read cover image %s: %s", cover_path, error)
            return "[dim]Cover image unavailable[/]"

        key = (cover_path, mtime, self.width, self.rows)
        if key not in self.cache:
            self.cache[key] = self._render_uncached(cover_path)

        return self.cache[key]

    def _render_uncached(self, cover_path: str) -> Text:
        chafa_path = shutil.which("chafa")
        if chafa_path is None:
            logger.warning("Unable to render cover image %s: chafa command not found", cover_path)
            return Text("Cover image unavailable: chafa missing", style="dim")

        command = [
            chafa_path,
            "--format=symbols",
            "--colors=full",
            "--dither=diffusion",
            "--preprocess=on",
            "--animate=off",
            "--label=off",
            "--relative=off",
            "--stretch",
            f"--size={self.width}x{self.rows}",
            cover_path,
        ]

        try:
            output = subprocess.check_output(command, text=True, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            reason = error.stderr.strip() if error.stderr else "chafa failed"
            logger.warning("Unable to render cover image %s: %s", cover_path, reason)
            return Text("Cover image unavailable", style="dim")

        return self._ansi_to_text(output.rstrip("\n"))

    def _ansi_to_text(self, value: str) -> Text:
        return Text("\n").join(AnsiDecoder().decode(value))
