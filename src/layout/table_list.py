from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, ListItem, ListView

from data import TableItem


class LauncherListItem(ListItem):
    def __init__(self, item: TableItem) -> None:
        super().__init__(Label(item.info.name))
        self.item = item


class TableList(VerticalScroll):
    def __init__(self, items: list[TableItem]) -> None:
        super().__init__(id="table-list-pane")
        self.items = items

    def compose(self) -> ComposeResult:
        yield Label("Tables", classes="pane-title")
        yield ListView(
            *(LauncherListItem(item) for item in self.items),
            id="table-list",
        )

    def select_first(self) -> None:
        if self.items:
            self.query_one(ListView).index = 0
