from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static
from pyfiglet import Figlet
from rich import box
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from cover_renderer import CoverRenderer
from data import TableItem
import theme
from vpin_data_store import TableStats

DEFAULT_TITLE_WIDTH = 120
TITLE_FONT = "small"


class TableDetails(VerticalScroll):
    def __init__(self, cover_renderer: CoverRenderer) -> None:
        super().__init__(id="table-details-pane")
        self.cover_renderer = cover_renderer

    def compose(self) -> ComposeResult:
        yield Static(id="table-title", classes="details-title")
        with Horizontal(id="details-overview"):
            yield Static(id="table-cover", classes="details-card")
            with Vertical(id="details-summary"):
                yield Static(id="table-stats", classes="details-card")
                yield Static(id="table-high-score", classes="details-card")
                yield Static("Description", classes="details-section-title")
                yield Static(id="table-description", classes="details-body")
                yield Static("Table Info", classes="details-section-title")
                yield Static(id="table-info", classes="details-body")

    def update_table(self, item: TableItem, stats: TableStats) -> None:
        title_widget = self.query_one("#table-title", Static)
        title_widget.update(self._format_title(item, title_widget.size.width or self.size.width))
        self._update_cover(item)
        self.query_one("#table-stats", Static).update(self._format_stats(stats))
        self.query_one("#table-high-score", Static).update(self._format_scores(item, stats))
        self.query_one("#table-info", Static).update(self._format_info(item))
        self.query_one("#table-description", Static).update(self._format_description(item))

    def _format_title(self, item: TableItem, width: int | None = None) -> Text:
        title = item.info.name or "Untitled Table"
        render_width = max(width or DEFAULT_TITLE_WIDTH, len(title), 1)
        rendered = Figlet(font=TITLE_FONT, width=render_width).renderText(title).rstrip()
        return Text(rendered, style=f"bold {theme.TITLE_TEXT}", no_wrap=True)

    def _update_cover(self, item: TableItem) -> None:
        overview = self.query_one("#details-overview", Horizontal)
        cover = self.query_one("#table-cover", Static)
        if not item.cover_path:
            overview.add_class("no-cover")
            cover.display = False
            cover.update("")
            return

        overview.remove_class("no-cover")
        cover.display = True
        cover.update(self.cover_renderer.render(item.cover_path))

    def _format_stats(self, stats: TableStats) -> str:
        last_played = self._format_date(stats.last_played_at) or "Never"
        return "\n".join(
            [
                f"[bold {theme.STATS_TITLE_TEXT}]Stats[/]",
                f"[dim]Launches:[/] {stats.launches_count}",
                f"[dim]Total Play Time:[/] {self._format_duration(stats.total_play_time_seconds)}",
                f"[dim]Last Played:[/] {last_played}",
            ]
        )

    def _format_scores(self, item: TableItem, stats: TableStats) -> Table | str:
        scores_to_show = stats.high_scores or item.scores
        first_seen_by_score = {score.identity(): score.first_seen_at for score in stats.high_scores}
        highlighted_score = next((score.identity() for score in stats.high_scores if score.first_seen_at), None)

        if not scores_to_show:
            return (
                f"[bold {theme.HIGH_SCORE_TITLE_TEXT}]High Scores[/]\n"
                f"[{theme.MUTED_TEXT}]No high scores found[/]"
            )

        scores = Table(
            title="High Scores",
            box=box.SIMPLE_HEAVY,
            expand=True,
            show_lines=False,
            title_style=f"bold {theme.HIGH_SCORE_TITLE_TEXT}",
        )
        scores.add_column("Name", ratio=3)
        scores.add_column("Initials", justify="center", no_wrap=True, ratio=1)
        scores.add_column("Score", justify="right", no_wrap=True, ratio=3)
        scores.add_column("Date", justify="right", no_wrap=True, ratio=2)

        for index, score in enumerate(scores_to_show):
            score_identity = (score.name, score.initials, score.score)
            style = f"bold {theme.TOP_HIGH_SCORE_TEXT}" if score_identity == highlighted_score else ""
            first_seen_at = first_seen_by_score.get(score_identity)
            scores.add_row(
                self._display_value(score.name) if self._has_value(score.name) else "Unknown",
                self._display_value(score.initials) if self._has_value(score.initials) else "-",
                self._display_value(score.score) if self._has_value(score.score) else "-",
                self._format_date(first_seen_at),
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
            return f"[{theme.MUTED_TEXT}]No table metadata available[/]"

        return "\n".join(available_fields)

    def _format_description(self, item: TableItem) -> str:
        if not self._has_value(item.info.description):
            return f"[{theme.MUTED_TEXT}]No description available.[/]"

        return escape(self._display_value(item.info.description))

    def _has_value(self, value: object) -> bool:
        if value is None:
            return False

        return str(value).strip().lower() not in {"", "none", "null"}

    def _display_value(self, value: object) -> str:
        return str(value).strip()

    def _format_duration(self, seconds: int) -> str:
        seconds = max(seconds, 0)
        hours, remainder = divmod(seconds, 3600)
        minutes, remaining_seconds = divmod(remainder, 60)

        if hours:
            return f"{hours}h {minutes}m"
        if minutes:
            return f"{minutes}m {remaining_seconds}s"
        return f"{remaining_seconds}s"

    def _format_date(self, value: str | None) -> str:
        if not value:
            return ""

        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return ""

        return f"{date.strftime('%b')} {date.day}, {date.year}"
