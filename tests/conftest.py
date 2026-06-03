import os

import pytest

from norn_ett.clickhouse import apply_raw_schema, get_client

DSN = os.environ.get("NORN_CLICKHOUSE_URL", "http://norn:norn@localhost:8123/norn_ett")


@pytest.fixture(scope="session")
def ch():
    client = get_client(DSN)
    apply_raw_schema(client)
    yield client
    client.close()


@pytest.fixture(autouse=True)
def _reset(ch):
    ch.command("TRUNCATE TABLE IF EXISTS raw_ett")
    yield
