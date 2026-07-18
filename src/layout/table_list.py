from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widgets import Label, ListItem, ListView

from controller import TABLE_NAVIGATION_BINDINGS
from data import TableItem


class LauncherListItem(ListItem):
    def __init__(self, item: TableItem) -> None:
        super().__init__(Label(item.info.name))
        self.item = item


class TableListView(ListView):
    BINDINGS = TABLE_NAVIGATION_BINDINGS

    class LaunchRequested(Message):
        def __init__(self, list_item: LauncherListItem) -> None:
            super().__init__()
            self.list_item = list_item

    def action_cursor_down(self) -> None:
        if not self.children:
            return

        if self.index is None or self.index == len(self.children) - 1:
            self.index = 0
        else:
            self.index += 1

    def action_cursor_up(self) -> None:
        if not self.children:
            return

        if self.index is None:
            self.index = 0
        elif self.index == 0:
            self.index = len(self.children) - 1
        elif self.index > 0:
            self.index -= 1

    def action_launch(self) -> None:
        if self.index is None or not self.children:
            return

        list_item = self.children[self.index]
        if isinstance(list_item, LauncherListItem):
            self.post_message(self.LaunchRequested(list_item))


class TableList(VerticalScroll):
    def __init__(self, items: list[TableItem]) -> None:
        super().__init__(id="table-list-pane")
        self.items = items

    def compose(self) -> ComposeResult:
        yield Label("Tables", classes="pane-title")
        yield TableListView(
            *(LauncherListItem(item) for item in self.items),
            id="table-list",
        )

    def select_first(self) -> None:
        list_view = self.query_one(TableListView)
        if self.items:
            list_view.index = 0
        list_view.focus()
