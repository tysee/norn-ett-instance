-- Per-point rolling-origin backtest from the latest calibration run: at each
-- past hour, what the model would have forecast (y_hat + p10/p90) vs what really
-- happened (y_actual). Written by `ett calibrate` and tagged model_name '… (backtest)'.
select
    metric_name,
    segment_key,
    forecast_ts as ts,
    horizon_step,
    y_hat, p10, p90, y_actual,
    abs(y_actual - y_hat) as error_abs,
    100 * abs(y_actual - y_hat) / y_actual as ape_pct
from {{ source('ett', 'forecast_point') }}
where metric_name = 'ot'
  and model_name like '%backtest%'
  and forecast_run_id = (
      select argMax(forecast_run_id, created_at)
      from {{ source('ett', 'forecast_point') }}
      where metric_name = 'ot' and model_name like '%backtest%'
  )
