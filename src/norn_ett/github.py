"""
src/norn_ett/github.py

Клиент сырых CSV-датасетов ETT из репозитория ETDataset на GitHub. Без авторизации.

Методы:
- fetch_rows(dataset, client=None) -> list[dict] — загрузка {dataset}.csv,
  разбор csv.DictReader, сортировка по возрастанию ts, типизация Float64.

Временные метки CSV наивные; трактуем их как UTC и помечаем tzinfo=UTC явно:
clickhouse-connect сдвигает наивные datetime на смещение машины при вставке.
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
