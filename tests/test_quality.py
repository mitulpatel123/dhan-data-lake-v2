from __future__ import annotations

import unittest

from dhan_data_lake.models import MarketBar
from dhan_data_lake.quality import assess_bars

from .test_core import VALID


class QualityTests(unittest.TestCase):
    def test_duplicate_natural_keys_fail_quality_gate(self) -> None:
        bar = MarketBar.from_mapping(VALID)
        report = assess_bars([bar, bar])
        self.assertFalse(report.passed)
        self.assertEqual(report.duplicate_keys, 1)


if __name__ == "__main__":
    unittest.main()
