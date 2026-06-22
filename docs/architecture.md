# Architecture and lineage

## Design goals

1. Reproduce the ingestion demonstration without private credentials.
2. Prevent duplicate market bars across retries.
3. Preserve failed source records for diagnosis.
4. Keep orchestration thin so business logic remains unit-testable.
5. Separate raw ingestion from analytics transformations.

## Lineage

| Stage | Input | Output | Quality control |
|---|---|---|---|
| Extract | CSV or approved provider adapter | Python mappings | Header and file checks |
| Validate | Source mapping | `MarketBar` | Required fields, timezone, OHLC and volume rules |
| Quarantine | Invalid mapping | `ingestion_quarantine` | Original JSON and explicit reason |
| Deduplicate | Valid bars | Natural-key batch | `(security_id, interval, event_time)` |
| Load | Deduplicated bars | `raw_market_bars` | PostgreSQL constraints and idempotent upsert |
| Transform | Raw table | dbt staging/mart | not-null and compound uniqueness tests |

## Failure handling

- Invalid rows are not silently discarded.
- A retry cannot create a second row for the same natural key.
- A corrected record updates the prior value and refreshes `ingested_at`.
- Unchanged records are counted separately from inserts and updates.

## Current boundary

The sample pipeline proves the data contract and operational behavior locally. Live DhanHQ REST/WebSocket ingestion, performance results, and cloud deployment are not yet accepted and must not be claimed as completed.
