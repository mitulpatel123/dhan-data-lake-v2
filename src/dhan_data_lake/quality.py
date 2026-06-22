"""Dataset-level quality checks used by tests and operational diagnostics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .models import MarketBar


@dataclass(frozen=True, slots=True)
class QualityReport:
    row_count: int
    duplicate_keys: int
    symbols: int
    passed: bool


def assess_bars(bars: Iterable[MarketBar]) -> QualityReport:
    materialized = list(bars)
    counts = Counter(bar.natural_key for bar in materialized)
    duplicates = sum(count - 1 for count in counts.values() if count > 1)
    return QualityReport(
        row_count=len(materialized),
        duplicate_keys=duplicates,
        symbols=len({bar.symbol for bar in materialized}),
        passed=bool(materialized) and duplicates == 0,
    )
