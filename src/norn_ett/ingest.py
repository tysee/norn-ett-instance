"""
src/norn_ett/ingest.py

Ingestion logic: write observations to raw_ett, full backfill (load all
datasets in their entirety) and incremental update from the latest ts.

Functions:
- write_rows(client, rows) -> int — insert observation rows.
- max_ts(client, dataset) -> datetime — latest ts in CH, tz-aware UTC
  (sentinel 1970-01-01 UTC).
- do_backfill(client, datasets) -> int — full dataset load.
- do_update(client, datasets) -> int — append rows newer than max_ts.
"""
from __future__ import annotations

from datetime import datetime, timezone

from norn_ett import github

_COLS = ["dataset", "ts", "hufl", "hull", "mufl", "mull", "lufl", "lull", "ot"]


def write_rows(client, rows: list[dict]) -> int:
    if not rows:
        return 0
    data = [[r[c] for c in _COLS] for r in rows]
    client.insert("raw_ett", data, column_names=_COLS)
    return len(rows)


def max_ts(client, dataset: str) -> datetime:
    res = client.query(
        "SELECT max(ts) FROM raw_ett WHERE dataset=%(d)s",
        parameters={"d": dataset},
    ).result_rows
    ts = res[0][0]
    if ts is None:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    # CH returns a naive UTC datetime — mark it explicitly so comparison with tz-aware ts works.
    return ts.replace(tzinfo=timezone.utc)


def do_backfill(client, datasets: list[str]) -> int:
    total = 0
    for dataset in datasets:
        rows = github.fetch_rows(dataset)
        total += write_rows(client, rows)
    return total


def do_update(client, datasets: list[str]) -> int:
    total = 0
    for dataset in datasets:
        since = max_ts(client, dataset)
        rows = [r for r in github.fetch_rows(dataset) if r["ts"] > since]
        total += write_rows(client, rows)
    return total
