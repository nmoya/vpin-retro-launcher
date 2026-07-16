import os

from config import Config
from data import TableItem
from vpxtool_bridge import VPXToolBridge


class TableManager:
    def __init__(self, config: Config) -> None:
        self.tables_root = config.tables_root
        self.vpxtool_bridge = VPXToolBridge(config.vpxtool_path)
        self.items = self.load_tables()

    def load_tables(self) -> list[TableItem]:
        items = []
        for root, _, files in os.walk(self.tables_root):
            for file in files:
                if file.endswith(".vpx"):
                    path = os.path.join(root, file)
                    info = self.vpxtool_bridge.info(path)
                    scores = self.vpxtool_bridge.scores(path)
                    items.append(TableItem(info=info, scores=scores))
        return items


if __name__ == "__main__":
    tables_root = "/home/nmoya/VPinball"
    manager = TableManager(tables_root)
    for item in manager.items:
        print(f"Title: {item.title}, System: {item.system}, Path: {item.path}")
