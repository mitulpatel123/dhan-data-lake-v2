CREATE TABLE IF NOT EXISTS raw_market_bars (
    security_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    exchange_segment TEXT NOT NULL,
    interval TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    open NUMERIC(20, 6) NOT NULL CHECK (open >= 0),
    high NUMERIC(20, 6) NOT NULL CHECK (high >= 0),
    low NUMERIC(20, 6) NOT NULL CHECK (low >= 0),
    close NUMERIC(20, 6) NOT NULL CHECK (close >= 0),
    volume BIGINT NOT NULL CHECK (volume >= 0),
    source TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (security_id, interval, event_time),
    CHECK (high >= open AND high >= close AND high >= low),
    CHECK (low <= open AND low <= close AND low <= high)
);

CREATE INDEX IF NOT EXISTS raw_market_bars_symbol_time_idx
    ON raw_market_bars (symbol, event_time DESC);

CREATE TABLE IF NOT EXISTS ingestion_quarantine (
    quarantine_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    raw_record JSONB NOT NULL,
    reason TEXT NOT NULL,
    quarantined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
