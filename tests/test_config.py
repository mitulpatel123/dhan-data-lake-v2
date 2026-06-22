from __future__ import annotations

import unittest

from dhan_data_lake.cli import build_parser


class CliConfigurationTests(unittest.TestCase):
    def test_dry_run_does_not_require_database_url(self) -> None:
        args = build_parser().parse_args(["--input", "sample.csv", "--dry-run"])
        self.assertTrue(args.dry_run)
        self.assertEqual(args.input, "sample.csv")


if __name__ == "__main__":
    unittest.main()
