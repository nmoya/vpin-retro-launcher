import hashlib
import os
from pathlib import Path

from rich.progress import BarColumn, Progress, TextColumn

from config import Config
from cover_renderer import CoverRenderer
from data import TableItem
from vpxtool_bridge import VPXToolBridge


class TableManager:
    def __init__(self, config: Config, cover_renderer: CoverRenderer) -> None:
        self.tables_root = config.tables_root
        self.vpxtool_bridge = VPXToolBridge(config.vpxtool_path)
        self.cover_renderer = cover_renderer
        self.items = self.load_tables()

    def load_tables(self) -> list[TableItem]:
        table_paths = self._table_paths()
        items = []

        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("Total: {task.total}"),
            TextColumn("Current: {task.fields[current_index]}"),
            TextColumn("Name: {task.fields[current_name]}"),
        ) as progress:
            task_id = progress.add_task(
                "Loading VPX tables",
                total=len(table_paths),
                current_index=0,
                current_name="",
            )

            for index, path in enumerate(table_paths, start=1):
                progress.update(task_id, current_index=index, current_name=os.path.basename(path))
                table_md5 = self._md5(path)
                info = self.vpxtool_bridge.info(path)
                progress.update(task_id, current_name=info.name or os.path.basename(path))
                scores = self.vpxtool_bridge.scores(path)
                cover_path = self._cover_path(path)
                if cover_path:
                    progress.update(task_id, current_name=f"Cover: {info.name or os.path.basename(path)}")
                    self.cover_renderer.precache(cover_path)
                items.append(TableItem(info=info, scores=scores, md5=table_md5, cover_path=cover_path))
                progress.advance(task_id)

        return sorted(items, key=lambda item: item.info.name.lower())

    def _table_paths(self) -> list[str]:
        table_paths = []
        for root, _, files in os.walk(self.tables_root):
            for file in files:
                if file.endswith(".vpx"):
                    table_paths.append(os.path.join(root, file))
        return sorted(table_paths)

    def _md5(self, path: str) -> str:
        digest = hashlib.md5()
        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _cover_path(self, table_path: str) -> str | None:
        table = Path(table_path)
        for filename in ("cover.jpg", "cover.jpeg", "cover.png"):
            cover_path = table.with_name(filename)
            if cover_path.is_file():
                return str(cover_path)

        return None


if __name__ == "__main__":
    tables_root = "/home/nmoya/VPinball"
    manager = TableManager(tables_root)
    for item in manager.items:
        print(f"Title: {item.title}, System: {item.system}, Path: {item.path}")
