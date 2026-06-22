from __future__ import annotations

import unittest
from copy import deepcopy

from dhan_data_lake.models import MarketBar, ValidationError
from dhan_data_lake.pipeline import IngestionPipeline
from dhan_data_lake.repositories import InMemoryRepository


VALID = {
    "security_id": "1333",
    "symbol": "HDFCBANK",
    "exchange_segment": "NSE_EQ",
    "interval": "1d",
    "event_time": "2026-06-15T00:00:00+05:30",
    "open": "100.00",
    "high": "110.00",
    "low": "95.00",
    "close": "108.00",
    "volume": "1000",
    "source": "test",
}


class MarketBarTests(unittest.TestCase):
    def test_valid_record_is_normalized(self) -> None:
        bar = MarketBar.from_mapping(VALID)
        self.assertEqual(bar.symbol, "HDFCBANK")
        self.assertIsNotNone(bar.event_time.tzinfo)

    def test_invalid_ohlc_is_rejected(self) -> None:
        raw = deepcopy(VALID)
        raw["high"] = "99"
        with self.assertRaisesRegex(ValidationError, "high"):
            MarketBar.from_mapping(raw)

    def test_timezone_is_required(self) -> None:
        raw = deepcopy(VALID)
        raw["event_time"] = "2026-06-15T00:00:00"
        with self.assertRaisesRegex(ValidationError, "timezone"):
            MarketBar.from_mapping(raw)


class PipelineTests(unittest.TestCase):
    def test_pipeline_deduplicates_and_quarantines(self) -> None:
        invalid = deepcopy(VALID)
        invalid["volume"] = "-1"
        repository = InMemoryRepository()
        report = IngestionPipeline(repository).run([VALID, VALID, invalid])
        self.assertEqual(report.source_rows, 3)
        self.assertEqual(report.accepted_rows, 1)
        self.assertEqual(report.duplicate_rows, 1)
        self.assertEqual(report.quarantined_rows, 1)
        self.assertEqual(report.upsert.inserted, 1)
        self.assertEqual(len(repository.quarantined), 1)

    def test_rerun_is_idempotent(self) -> None:
        repository = InMemoryRepository()
        pipeline = IngestionPipeline(repository)
        first = pipeline.run([VALID])
        second = pipeline.run([VALID])
        self.assertEqual(first.upsert.inserted, 1)
        self.assertEqual(second.upsert.unchanged, 1)
        self.assertEqual(len(repository.bars), 1)


if __name__ == "__main__":
    unittest.main()
