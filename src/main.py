import logging

from textual.app import App, ComposeResult
from textual.widgets import Header

from config import Config
from layout.horizontal_launcher import HorizontalLauncher
from table_manager import TableManager
from vpin_data_store import VPinDataStore

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


class VPinRetroLauncher(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #launcher {
        height: 1fr;
    }

    #table-list-pane,
    #table-details-pane {
        width: 1fr;
        height: 100%;
        border: solid $accent;
    }

    #table-list-pane {
        padding: 1;
    }

    #table-details-pane {
        padding: 1;
    }

    .details-title {
        width: 100%;
        margin-bottom: 1;
        color: $text;
        text-style: bold;
    }

    .details-card {
        width: 100%;
        margin-bottom: 1;
        padding: 1;
        border: tall $accent;
        background: $surface;
    }

    .details-section-title {
        margin-top: 1;
        color: $accent;
        text-style: bold;
    }

    .details-body {
        margin-top: 1;
        width: 100%;
    }

    #table-list {
        height: auto;
    }

    #table-details {
        width: 100%;
    }
    """

    def __init__(self, table_manager: TableManager, data_store: VPinDataStore, config: Config) -> None:
        super().__init__()
        self.table_manager = table_manager
        self.data_store = data_store
        self.config = config

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield HorizontalLauncher(
            self.table_manager.items,
            self.config.vpinball_path,
            self.table_manager.vpxtool_bridge,
            self.data_store,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    config = Config("./config.json")
    table_manager = TableManager(config)
    data_store = VPinDataStore("./vpin_data.json")
    for item in table_manager.items:
        data_store.import_table(item.md5, item.info.name or item.info.path, item.scores)

    VPinRetroLauncher(table_manager, data_store, config).run()


if __name__ == "__main__":
    main()
