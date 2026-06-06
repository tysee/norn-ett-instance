-- Feature-selection evidence: the LLM verdict per (source feature -> OT) pair from
-- the LATEST deps analysis of each pair, joined with the numeric method evidence
-- (lagged cross-correlation + Granger) that the verdict was judged on. One row per
-- explanation; is_real = 1 AND direction = 'source_leads' are the confirmed XReg
-- covariates that ot_timesfm_xreg auto-attaches.
with latest as (
    select source_segment, target_segment, argMax(analysis_run_id, created_at) as analysis_run_id
    from {{ source('ett', 'dependency_explanation') }}
    group by source_segment, target_segment
),
ev as (
    select
        analysis_run_id, source_segment, target_segment,
        anyIf(score, method = 'lagged_cross_correlation')  as xcorr_score,
        anyIf(lag, method = 'lagged_cross_correlation')    as xcorr_lag,
        anyIf(p_value, method = 'granger')                 as granger_p,
        anyIf(lag, method = 'granger')                     as granger_lag
    from {{ source('ett', 'metric_dependency') }}
    group by analysis_run_id, source_segment, target_segment
)
select
    e.source_segment as source_segment,
    e.target_segment as target_segment,
    e.lag,
    e.direction,
    e.is_real,
    e.confidence,
    e.explanation,
    e.caveats,
    e.llm_model,
    e.created_at,
    ev.xcorr_score,
    ev.xcorr_lag,
    ev.granger_p,
    ev.granger_lag
from {{ source('ett', 'dependency_explanation') }} as e
inner join latest
    on  latest.source_segment = e.source_segment
    and latest.target_segment = e.target_segment
    and latest.analysis_run_id = e.analysis_run_id
left join ev
    on  ev.analysis_run_id = e.analysis_run_id
    and ev.source_segment = e.source_segment
    and ev.target_segment = e.target_segment
