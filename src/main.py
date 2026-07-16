from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Header, Label, ListItem, ListView, Static


@dataclass(frozen=True)
class LauncherItem:
    title: str
    system: str
    description: str
    path: str


ITEMS = [
    LauncherItem(
        title="Attack from Mars",
        system="Visual Pinball X",
        description="A fast Williams-style table with alien invasion callouts.",
        path="tables/attack-from-mars.vpx",
    ),
    LauncherItem(
        title="Medieval Madness",
        system="Visual Pinball X",
        description="Castle-crashing fantasy pinball with trolls, jousts, and multiball.",
        path="tables/medieval-madness.vpx",
    ),
    LauncherItem(
        title="The Addams Family",
        system="Future Pinball",
        description="A mansion-themed table with quirky modes and memorable effects.",
        path="tables/addams-family.fpt",
    ),
]


class LauncherListItem(ListItem):
    def __init__(self, item: LauncherItem) -> None:
        super().__init__(Label(item.title))
        self.item = item


class TableList(VerticalScroll):
    def __init__(self, items: list[LauncherItem]) -> None:
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


class TableDetails(VerticalScroll):
    def __init__(self) -> None:
        super().__init__(id="table-details-pane")

    def compose(self) -> ComposeResult:
        yield Static(id="table-details")

    def update_table(self, item: LauncherItem) -> None:
        details = self.query_one(Static)
        details.update(
            f"[b]{item.title}[/b]\n\n"
            f"System: {item.system}\n"
            f"Path: {item.path}\n\n"
            f"{item.description}"
        )


class HorizontalLauncher(Horizontal):
    def __init__(self, items: list[LauncherItem]) -> None:
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


class LauncherApp(App[None]):
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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield HorizontalLauncher(ITEMS)


def main() -> None:
    LauncherApp().run()


if __name__ == "__main__":
    main()
