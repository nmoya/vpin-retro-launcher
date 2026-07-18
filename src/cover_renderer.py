import hashlib
import json
import logging
import os
from pathlib import Path
import subprocess

from rich.ansi import AnsiDecoder
from rich.text import Text

logger = logging.getLogger(__name__)

CACHE_VERSION = 1
COVER_ASPECT_WIDTH = 2
COVER_ASPECT_HEIGHT = 3
TERMINAL_CELL_WIDTH_TO_HEIGHT = 0.5
CHAFA_OPTIONS = [
    "--format=symbols",
    "--colors=full",
    "--dither=diffusion",
    "--preprocess=on",
    "--animate=off",
    "--label=off",
    "--relative=off",
    "--stretch",
]


class CoverRenderer:
    def __init__(self, chafa_path: str, width: int = 72, cache_dir: str = ".vpin_cache/covers") -> None:
        self.chafa_path = chafa_path
        self.width = width
        self.cache_dir = Path(cache_dir)
        self.cache: dict[str, Text] = {}

    @property
    def rows(self) -> int:
        visual_ratio = COVER_ASPECT_HEIGHT / COVER_ASPECT_WIDTH
        return max(round(self.width * visual_ratio * TERMINAL_CELL_WIDTH_TO_HEIGHT), 1)

    def render(self, cover_path: str | None) -> Text | str:
        if not cover_path:
            return ""

        stat = self._stat(cover_path)
        if stat is None:
            return "[dim]Cover image unavailable[/]"

        cache_key = self._cache_key(cover_path, stat)
        if cache_key not in self.cache:
            ansi = self._ansi_for_cover(cover_path, stat, cache_key)
            if ansi is None:
                return Text("Cover image unavailable", style="dim")
            self.cache[cache_key] = self._ansi_to_text(ansi)

        return self.cache[cache_key]

    def precache(self, cover_path: str | None) -> None:
        if not cover_path:
            return

        stat = self._stat(cover_path)
        if stat is None:
            return

        cache_key = self._cache_key(cover_path, stat)
        cache_path = self._cache_path(cache_key)
        if cache_path.is_file():
            return

        ansi = self._run_chafa(cover_path)
        if ansi is not None:
            self._write_cache(cache_path, ansi)

    def _ansi_for_cover(self, cover_path: str, stat: os.stat_result, cache_key: str) -> str | None:
        cache_path = self._cache_path(cache_key)
        try:
            if cache_path.is_file():
                return cache_path.read_text(encoding="utf-8")
        except OSError as error:
            logger.warning("Unable to read cover art cache %s: %s", cache_path, error)

        ansi = self._run_chafa(cover_path)
        if ansi is None:
            return None

        self._write_cache(cache_path, ansi)
        return ansi

    def _run_chafa(self, cover_path: str) -> str | None:
        command = [
            self.chafa_path,
            *CHAFA_OPTIONS,
            f"--size={self.width}x{self.rows}",
            cover_path,
        ]

        try:
            output = subprocess.check_output(command, text=True, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            reason = error.stderr.strip() if error.stderr else "chafa failed"
            logger.warning("Unable to render cover image %s: %s", cover_path, reason)
            return None
        except OSError as error:
            logger.warning("Unable to render cover image %s: %s", cover_path, error)
            return None

        return output.rstrip("\n")

    def _write_cache(self, cache_path: Path, ansi: str) -> None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = cache_path.with_suffix(".tmp")
            temp_path.write_text(ansi, encoding="utf-8")
            os.replace(temp_path, cache_path)
        except OSError as error:
            logger.warning("Unable to write cover art cache %s: %s", cache_path, error)

    def _cache_path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.ansi"

    def _cache_key(self, cover_path: str, stat: os.stat_result) -> str:
        key_data = {
            "version": CACHE_VERSION,
            "renderer": "chafa-cli",
            "chafa_path": self.chafa_path,
            "cover_path": str(Path(cover_path).resolve()),
            "mtime_ns": stat.st_mtime_ns,
            "size": stat.st_size,
            "width": self.width,
            "rows": self.rows,
            "aspect_width": COVER_ASPECT_WIDTH,
            "aspect_height": COVER_ASPECT_HEIGHT,
            "terminal_cell_width_to_height": TERMINAL_CELL_WIDTH_TO_HEIGHT,
            "chafa_options": CHAFA_OPTIONS,
        }
        encoded = json.dumps(key_data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _stat(self, cover_path: str) -> os.stat_result | None:
        try:
            return os.stat(cover_path)
        except OSError as error:
            logger.warning("Unable to read cover image %s: %s", cover_path, error)
            return None

    def _ansi_to_text(self, value: str) -> Text:
        return Text("\n").join(AnsiDecoder().decode(value))
