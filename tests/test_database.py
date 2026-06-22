from __future__ import annotations

import unittest
from copy import deepcopy

from dhan_data_lake.models import MarketBar
from dhan_data_lake.repositories import InMemoryRepository, migration_sql

from .test_core import VALID


def test_packaged_migration_is_available() -> None:
    migration = migration_sql()

    assert "CREATE TABLE IF NOT EXISTS raw_market_bars" in migration
    assert "CREATE TABLE IF NOT EXISTS ingestion_quarantine" in migration


class RepositoryContractTests(unittest.TestCase):
    def test_changed_record_is_updated_without_duplicate(self) -> None:
        repository = InMemoryRepository()
        original = MarketBar.from_mapping(VALID)
        changed_raw = deepcopy(VALID)
        changed_raw["close"] = "107.00"
        changed = MarketBar.from_mapping(changed_raw)

        repository.upsert_bars([original])
        stats = repository.upsert_bars([changed])

        self.assertEqual(stats.updated, 1)
        self.assertEqual(len(repository.bars), 1)
        self.assertEqual(next(iter(repository.bars.values())).close, changed.close)


if __name__ == "__main__":
    unittest.main()
