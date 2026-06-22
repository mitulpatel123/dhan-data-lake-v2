from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dhan_data_lake.ingestion import read_csv_records


class CsvReaderTests(unittest.TestCase):
    def test_reads_header_and_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bars.csv"
            path.write_text("security_id,symbol\n1,TEST\n", encoding="utf-8")
            self.assertEqual(list(read_csv_records(path)), [{"security_id": "1", "symbol": "TEST"}])

    def test_missing_file_is_explicit(self) -> None:
        with self.assertRaises(FileNotFoundError):
            list(read_csv_records("does-not-exist.csv"))


if __name__ == "__main__":
    unittest.main()
