-- Forecast points (joined to realized) PLUS the recent actual OT series, so a
-- single chart can show oil-temperature history alongside the forecast + interval.
--   * forecast rows: y_hat / p10 / p90 set, y_actual filled where realized exists
--   * actual rows:   y_actual = ot, y_hat/p10/p90 NULL (history for context)
-- Columns are unchanged from the original model, so the Lightdash explore needs
-- no re-deploy.
-- forecast_point keeps every run (audit history); show only the most recent
-- run (scalar subquery in WHERE — avoids ClickHouse legacy-analyzer CTE-join scoping).
with fc as (
    select
        f.metric_name, f.segment_key, f.forecast_ts as ts,
        f.y_hat, f.p10, f.p90,
        m.value as y_actual,
        abs(m.value - f.y_hat) as error_abs
    from {{ source('ett', 'forecast_point') }} as f
    left join {{ ref('mart_metric') }} as m
        on  m.metric_name = f.metric_name
        and m.segment_key = f.segment_key
        and m.ts = f.forecast_ts
        and m.feature = 'ot'
    where f.forecast_run_id = (
        select argMax(forecast_run_id, created_at)
        from {{ source('ett', 'forecast_point') }}
        where metric_name = 'ot' and model_name not like '%backtest%'
    )
),
actual as (
    select
        'ot' as metric_name, segment_key, ts,
        cast(null as Nullable(Float64)) as y_hat,
        cast(null as Nullable(Float64)) as p10,
        cast(null as Nullable(Float64)) as p90,
        ot as y_actual,
        cast(null as Nullable(Float64)) as error_abs
    from {{ ref('fct_ot') }}
    where ts >= (select max(ts) from {{ ref('fct_ot') }}) - interval 14 day
)
select metric_name, segment_key, ts, y_hat, p10, p90, y_actual, error_abs from fc
union all
select metric_name, segment_key, ts, y_hat, p10, p90, y_actual, error_abs from actual
