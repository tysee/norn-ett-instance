-- Backtest (rolling-origin) quality metrics per segment — the LATEST calibration
-- run of EACH model family, so baseline / timesfm / timesfm+xreg are comparable
-- side-by-side. forecast_segment has no model column; the model is recovered via
-- the run's backtest forecast_point rows (model_name '… (backtest)').
-- Values are pre-scaled to percent for direct display.
-- NB: aliases deliberately do NOT reuse source column names (bt_model/run_id):
-- the ClickHouse legacy analyzer substitutes same-named aliases into WHERE
-- (ILLEGAL_AGGREGATION on `any(model_name) as model_name` + WHERE model_name).
with run_model as (
    select
        forecast_run_id  as run_id,
        any(model_name)  as bt_model,
        max(created_at)  as last_created
    from {{ source('ett', 'forecast_point') }}
    where model_name like '%backtest%'
    group by forecast_run_id
),
latest_per_model as (
    select bt_model, argMax(run_id, last_created) as run_id
    from run_model
    group by bt_model
)
select
    l.bt_model as model_name,
    s.metric_name as metric_name,
    s.segment_key as segment_key,
    s.n_points as n_points,
    s.is_sparse as is_sparse,
    round(100 * s.coverage, 1) as coverage_pct,
    round(100 * s.mape, 2)     as mape_pct,
    round(100 * s.wape, 2)     as wape_pct,
    round(s.bias, 4)           as bias
from {{ source('ett', 'forecast_segment') }} as s
inner join latest_per_model as l
    on l.run_id = s.forecast_run_id
where s.metric_name = 'ot'
