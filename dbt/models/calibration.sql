-- Backtest (rolling-origin) quality metrics per segment, latest calibration run.
-- Values are pre-scaled to percent for direct display.
select
    metric_name,
    segment_key,
    n_points,
    is_sparse,
    round(100 * coverage, 1) as coverage_pct,
    round(100 * mape, 2)     as mape_pct,
    round(100 * wape, 2)     as wape_pct,
    round(bias, 4)           as bias
from {{ source('ett', 'forecast_segment') }}
where metric_name = 'ot'
  and forecast_run_id = (
      select argMax(forecast_run_id, created_at)
      from {{ source('ett', 'forecast_segment') }}
      where metric_name = 'ot'
  )
