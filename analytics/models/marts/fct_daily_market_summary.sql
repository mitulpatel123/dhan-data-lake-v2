select
    security_id,
    symbol,
    date(event_time) as trading_date,
    min(low) as daily_low,
    max(high) as daily_high,
    max(close) filter (
        where event_time = latest_event_time
    ) as closing_price,
    sum(volume) as total_volume,
    count(*) as bar_count
from (
    select
        *,
        max(event_time) over (
            partition by security_id, date(event_time)
        ) as latest_event_time
    from {{ ref('stg_market_bars') }}
) bars
group by security_id, symbol, date(event_time)
