from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from rich import box
from rich.markup import escape
from rich.table import Table

from data import TableItem


class TableDetails(VerticalScroll):
    def __init__(self) -> None:
        super().__init__(id="table-details-pane")

    def compose(self) -> ComposeResult:
        yield Static(id="table-title", classes="details-title")
        yield Static(id="table-high-score", classes="details-card")
        yield Static("Table Info", classes="details-section-title")
        yield Static(id="table-info", classes="details-body")
        yield Static("Description", classes="details-section-title")
        yield Static(id="table-description", classes="details-body")

    def update_table(self, item: TableItem) -> None:
        self.query_one("#table-title", Static).update(self._format_title(item))
        self.query_one("#table-high-score", Static).update(self._format_scores(item))
        self.query_one("#table-info", Static).update(self._format_info(item))
        self.query_one("#table-description", Static).update(self._format_description(item))

    def _format_title(self, item: TableItem) -> str:
        title = item.info.name or "Untitled Table"
        return f"[bold]{escape(title)}[/]"

    def _format_scores(self, item: TableItem) -> Table | str:
        if not item.scores:
            return "[bold yellow]High Scores[/]\n[dim]No high scores found[/]"

        scores = Table(
            title="High Scores",
            box=box.SIMPLE_HEAVY,
            expand=True,
            show_lines=False,
            title_style="bold yellow",
        )
        scores.add_column("Name", ratio=3)
        scores.add_column("Initials", justify="center", no_wrap=True, ratio=1)
        scores.add_column("Score", justify="right", no_wrap=True, ratio=3)

        for index, score in enumerate(item.scores):
            style = "bold green" if index == 0 else ""
            scores.add_row(
                self._display_value(score.name) if self._has_value(score.name) else "Unknown",
                self._display_value(score.initials) if self._has_value(score.initials) else "-",
                self._display_value(score.score) if self._has_value(score.score) else "-",
                style=style,
            )

        return scores

    def _format_info(self, item: TableItem) -> str:
        fields = [
            ("Table Version", item.info.version),
            ("VPX Version", item.info.vpx_version),
            ("Published", item.info.published_date),
            ("Revision", item.info.revision),
        ]
        available_fields = [
            f"[dim]{label}:[/] {escape(self._display_value(value))}"
            for label, value in fields
            if self._has_value(value)
        ]

        if not available_fields:
            return "[dim]No table metadata available[/]"

        return "\n".join(available_fields)

    def _format_description(self, item: TableItem) -> str:
        if not self._has_value(item.info.description):
            return "[dim]No description available.[/]"

        return escape(self._display_value(item.info.description))

    def _has_value(self, value: object) -> bool:
        if value is None:
            return False

        return str(value).strip().lower() not in {"", "none", "null"}

    def _display_value(self, value: object) -> str:
        return str(value).strip()
