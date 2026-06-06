"""
src/norn_ett/clickhouse.py

ClickHouse connection and raw_ett schema creation (idempotent).

Functions:
- parse_dsn(dsn) -> dict — parse a connection string.
- get_client(dsn=None) -> Client — client from DSN / env NORN_CLICKHOUSE_URL.
- apply_raw_schema(client) -> None — creates raw_ett (ReplacingMergeTree).
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

import clickhouse_connect
from clickhouse_connect.driver.client import Client

DEFAULT_DSN = "http://norn:norn@localhost:8123/norn_ett"

RAW_ETT_DDL = """
CREATE TABLE IF NOT EXISTS raw_ett (
    dataset     LowCardinality(String),
    ts          DateTime,
    hufl Float64, hull Float64, mufl Float64, mull Float64,
    lufl Float64, lull Float64, ot Float64,
    ingested_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(ingested_at)
ORDER BY (dataset, ts)
"""


def parse_dsn(dsn: str) -> dict:
    u = urlparse(dsn)
    database = u.path.lstrip("/")
    if not database:
        raise ValueError("ClickHouse DSN is missing the database path component")
    secure = u.scheme == "https"
    return {
        "host": u.hostname,
        "port": u.port or (8443 if secure else 8123),
        "username": u.username or "default",
        "password": u.password or "",
        "database": database,
        "secure": secure,
    }


def get_client(dsn: str | None = None) -> Client:
    cfg = parse_dsn(dsn or os.environ.get("NORN_CLICKHOUSE_URL", DEFAULT_DSN))
    return clickhouse_connect.get_client(**cfg)


def apply_raw_schema(client: Client) -> None:
    client.command(RAW_ETT_DDL)
