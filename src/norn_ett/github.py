"""
src/norn_ett/github.py

Client for raw ETT CSV datasets from the ETDataset repository on GitHub. No auth required.

Functions:
- fetch_rows(dataset, client=None) -> list[dict] — download {dataset}.csv,
  parse with csv.DictReader, sort by ts ascending, cast values to Float64.

CSV timestamps are naive; we treat them as UTC and explicitly set tzinfo=UTC:
clickhouse-connect shifts naive datetimes by the machine UTC offset on insert.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone

import httpx

DATASETS = ["ETTh1", "ETTh2", "ETTm1", "ETTm2"]
BASE_URL = "https://raw.githubusercontent.com/zhouhaoyi/ETDataset/main/ETT-small"


def _http_client() -> httpx.Client:
    return httpx.Client(timeout=60.0)


def fetch_rows(dataset: str, client: httpx.Client | None = None) -> list[dict]:
    owns = client is None
    client = client or _http_client()
    try:
        resp = client.get(f"{BASE_URL}/{dataset}.csv")
        resp.raise_for_status()
        rows: list[dict] = []
        for item in csv.DictReader(resp.text.splitlines()):
            rows.append(
                {
                    "dataset": dataset,
                    "ts": datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=timezone.utc
                    ),
                    "hufl": float(item["HUFL"]),
                    "hull": float(item["HULL"]),
                    "mufl": float(item["MUFL"]),
                    "mull": float(item["MULL"]),
                    "lufl": float(item["LUFL"]),
                    "lull": float(item["LULL"]),
                    "ot": float(item["OT"]),
                }
            )
        rows.sort(key=lambda r: r["ts"])
        return rows
    finally:
        if owns:
            client.close()
