"""
src/norn_ett/cli.py

CLI инстанса (typer): backfill полной истории и инкрементальный update наблюдений.

Команды:
- backfill --datasets ... — полная история в raw_ett.
- update --datasets ... — добор новых наблюдений.
"""
from __future__ import annotations

import typer

from norn_ett.clickhouse import apply_raw_schema, get_client
from norn_ett.github import DATASETS
from norn_ett.ingest import do_backfill, do_update

app = typer.Typer(help="norn-ett ingestion")

DEFAULT_DATASETS = list(DATASETS)


@app.command()
def backfill(
    datasets: list[str] = typer.Option(DEFAULT_DATASETS, "--datasets"),
) -> None:
    """Backfill the full ETT history into raw_ett."""
    client = get_client()
    apply_raw_schema(client)
    n = do_backfill(client, datasets)
    typer.echo(f"backfill complete: {n} rows written")


@app.command()
def update(
    datasets: list[str] = typer.Option(DEFAULT_DATASETS, "--datasets"),
) -> None:
    """Fetch and write rows newer than the latest stored ts."""
    client = get_client()
    apply_raw_schema(client)
    n = do_update(client, datasets)
    typer.echo(f"update complete: {n} rows written")
