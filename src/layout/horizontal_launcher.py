from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import ListView

from data import TableItem
from layout.table_details import TableDetails
from layout.table_list import LauncherListItem, TableList


class HorizontalLauncher(Horizontal):
    def __init__(self, items: list[TableItem]) -> None:
        super().__init__(id="launcher")
        self.items = items

    def compose(self) -> ComposeResult:
        yield TableList(self.items)
        yield TableDetails()

    def on_mount(self) -> None:
        if not self.items:
            return

        self.query_one(TableList).select_first()
        self.query_one(TableDetails).update_table(self.items[0])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, LauncherListItem):
            self.query_one(TableDetails).update_table(event.item.item)
