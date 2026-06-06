def test_parse_dsn_requires_db():
    import pytest

    from norn_ett.clickhouse import parse_dsn

    cfg = parse_dsn("http://norn:norn@localhost:8123/norn")
    assert cfg["host"] == "localhost" and cfg["database"] == "norn"
    with pytest.raises(ValueError):
        parse_dsn("http://u:p@h:8123/")


def test_raw_ett_columns(ch):
    cols = {r[0] for r in ch.query("DESCRIBE TABLE raw_ett").result_rows}
    assert {
        "dataset", "ts", "hufl", "hull", "mufl", "mull",
        "lufl", "lull", "ot", "ingested_at",
    } <= cols
