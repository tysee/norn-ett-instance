from datetime import datetime, timezone

from norn_ett.ingest import do_update, max_ts, write_rows


def _row(dataset, hour, ot):
    return {
        "dataset": dataset,
        "ts": datetime(2016, 7, 1, hour, 0, 0, tzinfo=timezone.utc),
        "hufl": float(ot), "hull": 2.0, "mufl": 4.5, "mull": 1.3,
        "lufl": 3.5, "lull": 1.1, "ot": float(ot),
    }


def test_write_rows_is_idempotent(ch):
    rows = [_row("ETTh1", h, 30 + h) for h in range(0, 3)]
    write_rows(ch, rows)
    write_rows(ch, rows)  # re-write same readings
    n = ch.query(
        "SELECT count() FROM (SELECT 1 FROM raw_ett FINAL "
        "WHERE dataset='ETTh1' GROUP BY dataset, ts)"
    ).result_rows[0][0]
    assert n == 3  # ReplacingMergeTree FINAL -> no duplicates


def test_max_ts_sentinel_then_real(ch):
    assert max_ts(ch, "ETTh1") == datetime(1970, 1, 1, tzinfo=timezone.utc)
    write_rows(ch, [_row("ETTh1", h, 30 + h) for h in range(0, 3)])
    assert max_ts(ch, "ETTh1") == datetime(2016, 7, 1, 2, 0, 0, tzinfo=timezone.utc)


def test_do_update_only_writes_newer(ch, monkeypatch):
    # Existing data up to hour 1; the feed returns hours 0..3.
    write_rows(ch, [_row("ETTh1", h, 30 + h) for h in range(0, 2)])

    feed = [_row("ETTh1", h, 30 + h) for h in range(0, 4)]
    import norn_ett.ingest as ingmod
    monkeypatch.setattr(ingmod.github, "fetch_rows", lambda dataset, client=None: feed)

    written = do_update(ch, ["ETTh1"])
    assert written == 2  # only hours 2 and 3 are newer than max_ts

    n = ch.query("SELECT count() FROM raw_ett FINAL WHERE dataset='ETTh1'").result_rows[0][0]
    assert n == 4
