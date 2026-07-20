from data import TableScore
from vpin_data_store import VPinDataStore


def test_missing_data_file_loads_empty_state(tmp_path):
    store = VPinDataStore(str(tmp_path / "vpin_data.json"))

    assert store.data.tables == {}


def test_invalid_json_loads_empty_state(tmp_path):
    data_path = tmp_path / "vpin_data.json"
    data_path.write_text("not json", encoding="utf-8")

    store = VPinDataStore(str(data_path))

    assert store.data.tables == {}


def test_import_table_stores_table_name_and_blank_score_dates(tmp_path):
    store = VPinDataStore(str(tmp_path / "vpin_data.json"))
    score = TableScore("Player One", "PO", "1000")

    store.import_table("abc123", "Attack From Mars", [score])

    stats = store.table_stats("abc123")
    assert stats.table_name == "Attack From Mars"
    assert stats.high_scores[0].first_seen_at is None


def test_update_high_scores_preserves_existing_and_timestamps_new_scores(tmp_path):
    store = VPinDataStore(str(tmp_path / "vpin_data.json"))
    imported_score = TableScore("Player One", "PO", "1000")
    new_score = TableScore("Player Two", "PT", "2000")

    store.import_table("abc123", "Attack From Mars", [imported_score])
    store.update_high_scores(
        "abc123",
        "Attack From Mars",
        [imported_score, new_score],
        timestamp="2026-10-06T12:00:00Z",
    )

    stats = VPinDataStore(str(tmp_path / "vpin_data.json")).table_stats("abc123")
    assert [score.first_seen_at for score in stats.high_scores] == [None, "2026-10-06T12:00:00Z"]


def test_score_identity_includes_initials_and_score(tmp_path):
    store = VPinDataStore(str(tmp_path / "vpin_data.json"))
    original = TableScore("Player One", "PO", "1000")
    same_name_new_score = TableScore("Player One", "PO", "2000")

    store.import_table("abc123", "Attack From Mars", [original])
    store.update_high_scores(
        "abc123",
        "Attack From Mars",
        [original, same_name_new_score],
        timestamp="2026-10-06T12:00:00Z",
    )

    stats = store.table_stats("abc123")
    assert [score.first_seen_at for score in stats.high_scores] == [None, "2026-10-06T12:00:00Z"]


def test_score_identity_preserves_timestamp_when_rank_name_changes(tmp_path):
    store = VPinDataStore(str(tmp_path / "vpin_data.json"))
    existing_score = TableScore("#1", "MOY", "1000")
    new_top_score = TableScore("#1", "MOY", "2000")
    shifted_score = TableScore("#2", "MOY", "1000")

    store.update_high_scores(
        "abc123",
        "The Goonies",
        [existing_score],
        timestamp="2026-10-05T12:00:00Z",
    )
    store.update_high_scores(
        "abc123",
        "The Goonies",
        [new_top_score, shifted_score],
        timestamp="2026-10-06T12:00:00Z",
    )

    stats = store.table_stats("abc123")
    assert [score.first_seen_at for score in stats.high_scores] == [
        "2026-10-06T12:00:00Z",
        "2026-10-05T12:00:00Z",
    ]


def test_record_launch_and_play_time_round_trip(tmp_path):
    data_path = tmp_path / "vpin_data.json"
    store = VPinDataStore(str(data_path))

    store.record_launch("abc123", "Attack From Mars", timestamp="2026-10-06T12:00:00Z")
    store.record_play_time("abc123", 90)
    store.record_play_time("abc123", -20)

    stats = VPinDataStore(str(data_path)).table_stats("abc123")
    assert stats.table_name == "Attack From Mars"
    assert stats.launches_count == 1
    assert stats.last_played_at == "2026-10-06T12:00:00Z"
    assert stats.total_play_time_seconds == 90
