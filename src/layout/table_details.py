from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from data import TableItem


class TableDetails(VerticalScroll):
    def __init__(self) -> None:
        super().__init__(id="table-details-pane")

    def compose(self) -> ComposeResult:
        yield Static(id="table-details")

    def update_table(self, item: TableItem) -> None:
        details = self.query_one(Static)
        details.update(
            f"[b]{item.info.name}[/b]\n\n"
            f"VPX Version: {item.info.vpx_version}\n"
            f"Path: {item.info.path}\n\n"
            f"{item.info.description}"
        )
