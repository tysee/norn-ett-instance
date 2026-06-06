-- Wide -> long: the 7 ETT channels (6 loads + oil temp) unpivoted per dataset.
-- Only the HOURLY datasets (ETTh1, ETTh2) — norn's grain is daily|hourly, so the
-- 15-min ETTm* series are excluded here. raw_ett is ReplacingMergeTree(ingested_at);
-- FINAL dedups re-ingested rows at read time (background merges are not guaranteed
-- to have collapsed dupes yet, and duplicate readings would skew deps/forecasts).
with base as (
    select dataset, ts, hufl, hull, mufl, mull, lufl, lull, ot
    from {{ source('ett', 'raw_ett') }} final
    where dataset in ('ETTh1', 'ETTh2')
)
select
    ts, dataset, feature,
    'reading' as metric_name,
    value,
    concat('dataset=', dataset, '|feature=', feature) as segment_key
from base
array join
    ['hufl', 'hull', 'mufl', 'mull', 'lufl', 'lull', 'ot'] as feature,
    [hufl, hull, mufl, mull, lufl, lull, ot]               as value
