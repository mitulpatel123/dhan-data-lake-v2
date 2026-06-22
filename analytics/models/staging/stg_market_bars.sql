select
    security_id,
    upper(symbol) as symbol,
    exchange_segment,
    interval,
    event_time,
    open,
    high,
    low,
    close,
    volume,
    source,
    ingested_at
from {{ source('raw', 'raw_market_bars') }}
