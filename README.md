# norn-ett-instance

ETT (Electricity Transformer Temperature) GitHub CSVs → ClickHouse `raw_ett` +
ETT dbt models for the norn forecasting platform. Linked into `norn` as a
submodule at `instances/ett/`.

## Quickstart

```
uv sync
uv run ett backfill           # 4 ETT CSVs -> raw_ett
CH_HOST=localhost uv run --with dbt-clickhouse dbt run --project-dir dbt --profiles-dir dbt
```

## End-to-end (manual integration)
Requires the norn platform + a running TimesFM worker (`deploy/timesfm.Dockerfile`,
`NORN_TIMESFM_URL`) for the `timesfm-2.5` jobs.
1. `uv run ett backfill` → `raw_ett` filled (all 4 datasets).
2. `CH_HOST=localhost uv run --with dbt-clickhouse dbt run --project-dir dbt --profiles-dir dbt` → `mart_metric` + `fct_ot`.
3. From norn: `uv run norn forecast .../forecasts/ot_baseline.yml` (or `ot_timesfm.yml`) → `forecast_point` filled.
4. `uv run norn deps .../forecasts/deps/*.yml` → discovers which load features lead OT (the `dependency_explanation` source_leads).
5. `NORN_FORECAST_COVARIATES__HORIZON_POLICY=ffill uv run norn forecast .../forecasts/ot_timesfm_xreg.yml` → re-forecasts OT with the confirmed leads as XReg covariates.
6. `uv run norn calibrate .../forecasts/ot_timesfm.yml` → `forecast_segment`.
7. MCP `get_forecast(metric="ot", segment="dataset=ETTh1|feature=ot")` returns rows; Lightdash shows actual-vs-forecast.

If the TimesFM worker is unreachable, the `timesfm-2.5` jobs **fail explicitly** (they record a
`forecast_run` row with `status=failed` and raise a clear error — there is no silent fallback).
To forecast without the worker, run `forecasts/ot_baseline.yml` (`model: baseline-seasonal-naive`),
or bring the worker up first.

## Dataset
[ETDataset](https://github.com/zhouhaoyi/ETDataset) (ETT-small), 4 CSV files:

| file    | grain  | rows  |
|---------|--------|-------|
| `ETTh1` | hourly | 17420 |
| `ETTh2` | hourly | 17420 |
| `ETTm1` | 15-min | 69680 |
| `ETTm2` | 15-min | 69680 |

Columns: `date,HUFL,HULL,MUFL,MULL,LUFL,LULL,OT` — `OT` is **oil temperature**
(the forecast target); the other 6 are load covariates (high/middle/low useful &
useless load). Date range is `2016-07-01 00:00:00 .. 2018-06-26` (tz-naive,
treated as UTC).

License note: the repo's `LICENSE` file is **CC BY-ND 4.0**, while the README
states **CC BY 4.0** — a discrepancy in the upstream source worth flagging.

Only **ETTh1** and **ETTh2** (the hourly datasets) are exposed in the marts:
norn's grain contract supports `daily|hourly` only, so the 15-min `ETTm*` files
are ingested into `raw_ett` but not unpivoted into `mart_metric`.
