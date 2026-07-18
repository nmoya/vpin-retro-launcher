from data import TableInfo, TableItem
from main import sort_tables_by_recent
from vpin_data_store import VPinDataStore


def table_item(name, md5):
    return TableItem(
        info=TableInfo(
            name=name,
            vpx_version="",
            version="",
            published_date="",
            revision="",
            description="",
            path=f"/{name}.vpx",
        ),
        scores=[],
        md5=md5,
    )


def test_sort_tables_by_recent_then_alphabetical(tmp_path):
    data_store = VPinDataStore(str(tmp_path / "vpin_data.json"))
    alpha = table_item("Alpha", "alpha")
    beta = table_item("Beta", "beta")
    zulu = table_item("Zulu", "zulu")
    delta = table_item("Delta", "delta")
    gamma = table_item("Gamma", "gamma")
    items = [gamma, zulu, beta, delta, alpha]

    data_store.record_launch("zulu", "Zulu", timestamp="2026-10-05T12:00:00Z")
    data_store.record_launch("beta", "Beta", timestamp="2026-10-06T12:00:00Z")
    data_store.record_launch("alpha", "Alpha", timestamp="2026-10-06T12:00:00Z")

    sort_tables_by_recent(items, data_store)

    assert [item.info.name for item in items] == ["Alpha", "Beta", "Zulu", "Delta", "Gamma"]
