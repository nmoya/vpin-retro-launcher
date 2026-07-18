import logging
import os

from textual.app import App, ComposeResult
from textual.css.query import NoMatches
from textual.widgets import Header, Static

from config import Config
from gamepad_controller import GamepadController
from layout.horizontal_launcher import HorizontalLauncher
from layout.table_list import TableListView
from table_manager import TableManager
from vpin_data_store import VPinDataStore

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
GAMEPAD_POLL_SECONDS = 1 / 60


class VPinRetroLauncher(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #launcher {
        height: 1fr;
    }

    #controls-footer {
        height: 1;
        padding: 0 1;
        background: $surface;
        color: $text-muted;
        text-style: bold;
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
        self.gamepad_controller: GamepadController | None = None
        self.gamepad_timer = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield HorizontalLauncher(
            self.table_manager.items,
            self.config.vpinball_path,
            self.table_manager.vpxtool_bridge,
            self.data_store,
        )
        yield Static(
            "Up: Up / K / W / L / R2 / D-pad / Left Stick    "
            "Down: Down / J / S / A / L2 / D-pad / Left Stick    "
            "Launch: Enter / Circle",
            id="controls-footer",
        )

    def on_mount(self) -> None:
        self.gamepad_controller = GamepadController(
            cursor_down=self._gamepad_cursor_down,
            cursor_up=self._gamepad_cursor_up,
            launch=self._gamepad_launch,
        )
        self.gamepad_controller.start()
        self.gamepad_timer = self.set_interval(GAMEPAD_POLL_SECONDS, self.gamepad_controller.poll)

    def on_unmount(self) -> None:
        if self.gamepad_timer is not None:
            self.gamepad_timer.stop()

        if self.gamepad_controller is not None:
            self.gamepad_controller.stop()

    def _gamepad_cursor_down(self) -> None:
        list_view = self._table_list_view()
        if list_view is not None:
            list_view.action_cursor_down()

    def _gamepad_cursor_up(self) -> None:
        list_view = self._table_list_view()
        if list_view is not None:
            list_view.action_cursor_up()

    def _gamepad_launch(self) -> None:
        list_view = self._table_list_view()
        if list_view is not None:
            list_view.action_launch()

    def _table_list_view(self) -> TableListView | None:
        try:
            return self.query_one(TableListView)
        except NoMatches:
            return None


def main() -> None:
    log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    config = Config("./config.json")
    table_manager = TableManager(config)
    data_store = VPinDataStore("./vpin_data.json")
    for item in table_manager.items:
        data_store.import_table(item.md5, item.info.name or item.info.path, item.scores)

    VPinRetroLauncher(table_manager, data_store, config).run()


if __name__ == "__main__":
    main()
