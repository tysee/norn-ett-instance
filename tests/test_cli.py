from typer.testing import CliRunner

from norn_ett.cli import app

runner = CliRunner()

_CSV = (
    "date,HUFL,HULL,MUFL,MULL,LUFL,LULL,OT\n"
    "2016-07-01 00:00:00,5.8,2.0,4.6,1.3,3.7,1.2,30.9\n"
    "2016-07-01 01:00:00,5.7,2.0,4.5,1.3,3.6,1.1,30.7\n"
)


def test_backfill_command(ch, monkeypatch):
    import httpx

    def handler(req):
        return httpx.Response(200, text=_CSV)

    # Patch the github client factory to use a mock transport.
    import norn_ett.github as ghmod
    monkeypatch.setattr(
        ghmod, "_http_client",
        lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setenv("NORN_CLICKHOUSE_URL", "http://norn:norn@localhost:8123/norn_ett")

    result = runner.invoke(app, ["backfill", "--datasets", "ETTh1"])
    assert result.exit_code == 0, result.output
    assert "rows" in result.output.lower()
