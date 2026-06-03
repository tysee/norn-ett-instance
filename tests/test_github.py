from datetime import datetime, timezone

import httpx

from norn_ett.github import fetch_rows

# ETDataset CSV: date,HUFL,HULL,MUFL,MULL,LUFL,LULL,OT — rows deliberately out of order.
_CSV = (
    "date,HUFL,HULL,MUFL,MULL,LUFL,LULL,OT\n"
    "2016-07-01 02:00:00,5.6,2.0,4.5,1.3,3.5,1.1,30.5\n"  # latest
    "2016-07-01 00:00:00,5.8,2.0,4.6,1.3,3.7,1.2,30.9\n"  # earliest
    "2016-07-01 01:00:00,5.7,2.0,4.5,1.3,3.6,1.1,30.7\n"  # middle
)


def test_fetch_rows_sorts_and_types():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_CSV)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    rows = fetch_rows("ETTh1", client=client)

    # ts is naive-UTC to match the ClickHouse DateTime column / ingest, ascending.
    assert [r["ts"] for r in rows] == [
        datetime(2016, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        datetime(2016, 7, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2016, 7, 1, 2, 0, 0, tzinfo=timezone.utc),
    ]
    assert all(r["ts"].tzinfo == timezone.utc for r in rows)
    assert rows[0]["ot"] == 30.9 and rows[0]["hufl"] == 5.8
    assert all(isinstance(r[k], float) for r in rows for k in
               ("hufl", "hull", "mufl", "mull", "lufl", "lull", "ot"))
    assert all(r["dataset"] == "ETTh1" for r in rows)


def test_fetch_rows_calls_dataset_url():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["url"] = str(req.url)
        return httpx.Response(200, text=_CSV)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetch_rows("ETTh1", client=client)
    assert "ETTh1.csv" in seen["url"]
