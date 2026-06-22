"""Persistence adapters with a deterministic idempotency contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Iterable, Protocol

from .models import MarketBar


def migration_sql() -> str:
    """Return the bundled PostgreSQL schema for installed and source builds."""

    return files("dhan_data_lake").joinpath("sql/001_init.sql").read_text(encoding="utf-8")


@dataclass(frozen=True, slots=True)
class UpsertStats:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


class MarketBarRepository(Protocol):
    def upsert_bars(self, bars: Iterable[MarketBar]) -> UpsertStats: ...

    def quarantine(self, raw_record: dict[str, Any], reason: str) -> None: ...


class InMemoryRepository:
    """Test adapter that implements the same natural-key behavior as PostgreSQL."""

    def __init__(self) -> None:
        self.bars: dict[tuple[Any, ...], MarketBar] = {}
        self.quarantined: list[tuple[dict[str, Any], str]] = []

    def upsert_bars(self, bars: Iterable[MarketBar]) -> UpsertStats:
        inserted = updated = unchanged = 0
        for bar in bars:
            current = self.bars.get(bar.natural_key)
            if current is None:
                inserted += 1
                self.bars[bar.natural_key] = bar
            elif current == bar:
                unchanged += 1
            else:
                updated += 1
                self.bars[bar.natural_key] = bar
        return UpsertStats(inserted, updated, unchanged)

    def quarantine(self, raw_record: dict[str, Any], reason: str) -> None:
        self.quarantined.append((dict(raw_record), reason))


class PostgresRepository:
    """PostgreSQL adapter; connections are opened only for individual operations."""

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("DATABASE_URL is required")
        self.dsn = dsn

    def initialize(self) -> None:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            connection.execute(migration_sql())

    def upsert_bars(self, bars: Iterable[MarketBar]) -> UpsertStats:
        import psycopg

        statement = """
            INSERT INTO raw_market_bars (
                security_id, symbol, exchange_segment, interval, event_time,
                open, high, low, close, volume, source
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (security_id, interval, event_time) DO UPDATE SET
                symbol = EXCLUDED.symbol,
                exchange_segment = EXCLUDED.exchange_segment,
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                source = EXCLUDED.source,
                ingested_at = CURRENT_TIMESTAMP
            WHERE (raw_market_bars.symbol, raw_market_bars.exchange_segment,
                   raw_market_bars.open, raw_market_bars.high, raw_market_bars.low,
                   raw_market_bars.close, raw_market_bars.volume, raw_market_bars.source)
              IS DISTINCT FROM
                  (EXCLUDED.symbol, EXCLUDED.exchange_segment,
                   EXCLUDED.open, EXCLUDED.high, EXCLUDED.low,
                   EXCLUDED.close, EXCLUDED.volume, EXCLUDED.source)
            RETURNING (xmax = 0) AS inserted
        """
        inserted = updated = unchanged = 0
        with psycopg.connect(self.dsn) as connection:
            for bar in bars:
                result = connection.execute(
                    statement,
                    (
                        bar.security_id,
                        bar.symbol,
                        bar.exchange_segment,
                        bar.interval,
                        bar.event_time,
                        bar.open,
                        bar.high,
                        bar.low,
                        bar.close,
                        bar.volume,
                        bar.source,
                    ),
                ).fetchone()
                if result is None:
                    unchanged += 1
                elif result[0]:
                    inserted += 1
                else:
                    updated += 1
        return UpsertStats(inserted, updated, unchanged)

    def quarantine(self, raw_record: dict[str, Any], reason: str) -> None:
        import psycopg

        with psycopg.connect(self.dsn) as connection:
            connection.execute(
                "INSERT INTO ingestion_quarantine (raw_record, reason) VALUES (%s::jsonb, %s)",
                (json.dumps(raw_record, default=str), reason),
            )
