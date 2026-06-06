import subprocess
from datetime import datetime, timezone


def _seed(ch):
    rows = []
    for h in range(0, 3):  # 3 consecutive hours of ETTh1
        v = 30.0 + h
        rows.append(["ETTh1", datetime(2016, 7, 1, h, tzinfo=timezone.utc), v + 0.1, 2.0, v + 0.2, 1.3, v + 0.3, 1.1, v])
    # One ETTm1 row — must be EXCLUDED from the (hourly-only) mart.
    rows.append(["ETTm1", datetime(2016, 7, 1, 0, 15, tzinfo=timezone.utc), 5.0, 2.0, 4.5, 1.3, 3.5, 1.1, 30.0])
    ch.insert(
        "raw_ett", rows,
        column_names=["dataset", "ts", "hufl", "hull", "mufl", "mull", "lufl", "lull", "ot"],
    )


def _dbt(cmd, *args):
    # --select limits the build to raw_ett-backed marts: the contract-table views
    # (calibration/actual_vs_forecast/...) reference platform tables that do not
    # exist in the isolated test DB (they are created by the norn platform).
    return subprocess.run(
        ["uv", "run", "--with", "dbt-clickhouse", "dbt", cmd, *args,
         "--project-dir", "dbt", "--profiles-dir", "dbt"],
        capture_output=True, text=True, env={**_env()},
    )


def _env():
    import os
    from urllib.parse import urlparse

    from conftest import DSN

    # Build dbt models into the SAME database the test fixture seeds/queries —
    # so pointing NORN_CLICKHOUSE_URL at an isolated DB isolates dbt too
    # (never truncate/build over the live norn_ett by accident).
    schema = urlparse(DSN).path.lstrip("/") or "norn_ett"
    return {**os.environ, "CH_HOST": "localhost", "CH_SCHEMA": schema}


def test_mart_metric_derivations(ch):
    _seed(ch)
    r = _dbt("run", "--select", "mart_metric", "fct_ot")
    assert r.returncode == 0, r.stdout + r.stderr

    # metric_name is the constant 'reading'.
    names = ch.query("SELECT DISTINCT metric_name FROM mart_metric").result_rows
    assert names == [("reading",)]

    # OT segment_key is present and well-formed.
    seg = ch.query(
        "SELECT DISTINCT segment_key FROM mart_metric WHERE dataset='ETTh1' AND feature='ot'"
    ).result_rows
    assert seg == [("dataset=ETTh1|feature=ot",)]

    # 7 features unpivoted per ts per dataset.
    per_ts = ch.query(
        "SELECT count(DISTINCT feature) FROM mart_metric WHERE dataset='ETTh1' AND ts='2016-07-01 00:00:00'"
    ).result_rows[0][0]
    assert per_ts == 7

    # Hourly-only mart: no ETTm1 rows.
    m1 = ch.query("SELECT count() FROM mart_metric WHERE dataset='ETTm1'").result_rows[0][0]
    assert m1 == 0

    # fct_ot exposes only the ot feature.
    feats = ch.query("SELECT DISTINCT feature FROM fct_ot").result_rows
    assert feats == [("ot",)]
