from dataclasses import replace
import hashlib
import logging
import time

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import ListView

from cover_renderer import CoverRenderer
from data import TableItem
from gamepad_controller import GamepadController
from layout.table_details import TableDetails
from layout.table_list import LauncherListItem, TableList, TableListView
from vpin_data_store import VPinDataStore, utc_now
from vpinball_runner import VPinballRunner
from vpxtool_bridge import VPXToolBridge


logger = logging.getLogger(__name__)
LAUNCH_SUPPRESSION_SECONDS = 1.0


class HorizontalLauncher(Horizontal):
    def __init__(
        self,
        items: list[TableItem],
        vpinball_path: str,
        vpxtool_bridge: VPXToolBridge,
        data_store: VPinDataStore,
        gamepad_controller: GamepadController,
        cover_renderer: CoverRenderer,
    ) -> None:
        super().__init__(id="launcher")
        self.items = items
        self.vpinball_path = vpinball_path
        self.vpxtool_bridge = vpxtool_bridge
        self.data_store = data_store
        self.gamepad_controller = gamepad_controller
        self.cover_renderer = cover_renderer
        self.launch_in_progress = False
        self.last_launch_finished_at = 0.0

    def compose(self) -> ComposeResult:
        yield TableList(self.items)
        yield TableDetails(self.cover_renderer)

    def on_mount(self) -> None:
        if not self.items:
            return

        self.query_one(TableList).select_first()
        self._update_details(self.items[0])

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if isinstance(event.item, LauncherListItem):
            self._update_details(event.item.item)

    def on_table_list_view_launch_requested(self, event: TableListView.LaunchRequested) -> None:
        self.launch_table(event.list_item)

    def launch_selected_table(self) -> None:
        list_view = self.query_one(TableListView)
        if list_view.index is None or not list_view.children:
            return

        list_item = list_view.children[list_view.index]
        if isinstance(list_item, LauncherListItem):
            self.launch_table(list_item)

    def launch_table(self, list_item: LauncherListItem) -> None:
        now = time.monotonic()
        if self.launch_in_progress or now - self.last_launch_finished_at < LAUNCH_SUPPRESSION_SECONDS:
            logger.info("Ignoring duplicate launch request")
            return

        self.launch_in_progress = True
        try:
            self._launch_table(list_item)
        finally:
            self.launch_in_progress = False
            self.last_launch_finished_at = time.monotonic()

    def _launch_table(self, list_item: LauncherListItem) -> None:
        item = list_item.item
        table_path = item.info.path
        current_md5 = self._md5(table_path)

        if current_md5 != item.md5:
            logger.warning(
                "Table changed since loading: %s loaded_md5=%s current_md5=%s",
                table_path,
                item.md5,
                current_md5,
            )
            self.app.notify(
                "This table changed since loading. Stats will be tracked as a new table version.",
                severity="warning",
            )
            self.data_store.import_table(
                current_md5,
                self._table_name(item),
                self.vpxtool_bridge.scores(table_path),
            )

        launched_at = utc_now()
        self.data_store.record_launch(current_md5, self._table_name(item), launched_at)
        start_time = time.monotonic()

        with self.app.suspend():
            VPinballRunner(self.vpinball_path, self.gamepad_controller.poll_events).run(table_path)

        play_seconds = int(time.monotonic() - start_time)
        self.data_store.record_play_time(current_md5, play_seconds)
        scores = self.vpxtool_bridge.scores(table_path)
        self.data_store.update_high_scores(current_md5, self._table_name(item), scores)

        updated_item = replace(item, scores=scores, md5=current_md5)
        list_item.item = updated_item
        for index, existing_item in enumerate(self.items):
            if existing_item is item:
                self.items[index] = updated_item
                break

        self._update_details(updated_item)

    def _update_details(self, item: TableItem) -> None:
        self.query_one(TableDetails).update_table(item, self.data_store.table_stats(item.md5))

    def _table_name(self, item: TableItem) -> str:
        return item.info.name or item.info.path

    def _md5(self, path: str) -> str:
        digest = hashlib.md5()
        with open(path, "rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
