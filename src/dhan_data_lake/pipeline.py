"""Validation, quarantine, deduplication, and idempotent persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .models import MarketBar, ValidationError
from .repositories import MarketBarRepository, UpsertStats


@dataclass(frozen=True, slots=True)
class PipelineReport:
    source_rows: int
    accepted_rows: int
    duplicate_rows: int
    quarantined_rows: int
    upsert: UpsertStats

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        return result


class IngestionPipeline:
    def __init__(self, repository: MarketBarRepository) -> None:
        self.repository = repository

    def run(self, records: Iterable[dict[str, Any]]) -> PipelineReport:
        deduplicated: dict[tuple[Any, ...], MarketBar] = {}
        source_rows = duplicate_rows = quarantined_rows = 0

        for raw in records:
            source_rows += 1
            try:
                bar = MarketBar.from_mapping(raw)
            except ValidationError as exc:
                quarantined_rows += 1
                self.repository.quarantine(raw, str(exc))
                continue
            if bar.natural_key in deduplicated:
                duplicate_rows += 1
            deduplicated[bar.natural_key] = bar

        stats = self.repository.upsert_bars(deduplicated.values())
        return PipelineReport(
            source_rows=source_rows,
            accepted_rows=len(deduplicated),
            duplicate_rows=duplicate_rows,
            quarantined_rows=quarantined_rows,
            upsert=stats,
        )
