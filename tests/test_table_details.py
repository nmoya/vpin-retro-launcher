from layout.table_details import TableDetails


def test_format_date_returns_blank_for_none_or_invalid_values():
    details = TableDetails()

    assert details._format_date(None) == ""
    assert details._format_date("") == ""
    assert details._format_date("not a date") == ""


def test_format_date_uses_short_month_day_year():
    details = TableDetails()

    assert details._format_date("2026-10-06T12:00:00Z") == "Oct 6, 2026"


def test_format_duration():
    details = TableDetails()

    assert details._format_duration(0) == "0s"
    assert details._format_duration(65) == "1m 5s"
    assert details._format_duration(3660) == "1h 1m"
    assert details._format_duration(-1) == "0s"
