import os
import re

import pytest

from norn_ett.clickhouse import apply_raw_schema, get_client

DSN = os.environ.get("NORN_CLICKHOUSE_URL", "http://norn:norn@localhost:8123/norn_ett_test")

# Destructive-test guard: the autouse fixture below TRUNCATEs raw_ett in whatever
# DB the DSN points at. Refuse anything that does not look like a dedicated test
# DB so a missing env var can never wipe the live norn_ett.
_TEST_DB = DSN.rstrip("/").rsplit("/", 1)[-1]
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", _TEST_DB) or not _TEST_DB.endswith("_test"):
    raise RuntimeError(
        f"refusing to run the test suite against database {_TEST_DB!r}: tests truncate "
        "raw_ett. Point NORN_CLICKHOUSE_URL at a dedicated *_test database."
    )


def _ensure_test_db() -> None:
    """Create the isolated test DB if missing (connect via the server's default DB)."""
    base = DSN.rstrip("/").rsplit("/", 1)[0]
    bootstrap = get_client(f"{base}/default")
    bootstrap.command(f"CREATE DATABASE IF NOT EXISTS {_TEST_DB}")
    bootstrap.close()


@pytest.fixture(scope="session")
def ch():
    _ensure_test_db()
    client = get_client(DSN)
    apply_raw_schema(client)
    yield client
    client.close()


@pytest.fixture(autouse=True)
def _reset(ch):
    ch.command("TRUNCATE TABLE IF EXISTS raw_ett")
    yield
