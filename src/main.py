import logging

from textual.app import App, ComposeResult
from textual.widgets import Header

from config import Config
from layout.horizontal_launcher import HorizontalLauncher
from table_manager import TableManager


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
        padding: 1 2;
    }

    #table-list {
        height: auto;
    }

    #table-details {
        width: 100%;
    }
    """

    def __init__(self, table_manager: TableManager) -> None:
        super().__init__()
        self.table_manager = table_manager

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield HorizontalLauncher(self.table_manager.items)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

    config = Config("./config.json")
    table_manager = TableManager(config)
    VPinRetroLauncher(table_manager).run()


if __name__ == "__main__":
    main()
