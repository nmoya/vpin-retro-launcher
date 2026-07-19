from cover_renderer import CoverRenderer
from data import TableInfo, TableItem
from layout.table_details import TableDetails
import theme
from vpin_data_store import HighScoreRecord, TableStats


def table_details():
    return TableDetails(CoverRenderer("chafa"))


def test_format_date_returns_blank_for_none_or_invalid_values():
    details = table_details()

    assert details._format_date(None) == ""
    assert details._format_date("") == ""
    assert details._format_date("not a date") == ""


def test_format_date_uses_short_month_day_year():
    details = table_details()

    assert details._format_date("2026-10-06T12:00:00Z") == "Oct 6, 2026"


def test_format_duration():
    details = table_details()

    assert details._format_duration(0) == "0s"
    assert details._format_duration(65) == "1m 5s"
    assert details._format_duration(3660) == "1h 1m"
    assert details._format_duration(-1) == "0s"


def test_format_title_uses_large_ascii_rendering():
    details = table_details()
    title = details._format_title(table_item())

    assert "Table" not in title.plain
    assert "\n" in title.plain


def test_format_title_uses_available_width_without_changing_font():
    details = table_details()
    item = table_item("Jurassic Park Data East")

    narrow_title = details._format_title(item, width=30)
    wide_title = details._format_title(item, width=120)

    assert len(wide_title.plain.splitlines()) < len(narrow_title.plain.splitlines())
    assert max(len(line) for line in wide_title.plain.splitlines()) <= 120


def test_format_scores_highlights_first_score_with_first_seen_at():
    details = table_details()
    item = table_item()
    stats = TableStats(
        high_scores=[
            HighScoreRecord("Imported", "IMP", "1000", None),
            HighScoreRecord("New", "NEW", "2000", "2026-10-06T12:00:00Z"),
            HighScoreRecord("Newer", "NWR", "3000", "2026-10-07T12:00:00Z"),
        ]
    )

    table = details._format_scores(item, stats)

    assert [row.style for row in table.rows] == ["", f"bold {theme.TOP_HIGH_SCORE_TEXT}", ""]


def test_format_scores_does_not_highlight_imported_scores():
    details = table_details()
    item = table_item()
    stats = TableStats(
        high_scores=[
            HighScoreRecord("Imported", "IMP", "1000", None),
            HighScoreRecord("Also Imported", "IMP", "2000", None),
        ]
    )

    table = details._format_scores(item, stats)

    assert [row.style for row in table.rows] == ["", ""]


def table_item(name="Table"):
    return TableItem(
        info=TableInfo(
            name=name,
            vpx_version="",
            version="",
            published_date="",
            revision="",
            description="",
            path="/table.vpx",
        ),
        scores=[],
        md5="abc123",
    )
