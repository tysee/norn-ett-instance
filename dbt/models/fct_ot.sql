select ts, dataset, feature, value as ot, segment_key
from {{ ref('mart_metric') }} where feature = 'ot'
