"""Run a credential-free integrity assessment for a CSV dataset."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from dhan_data_lake.ingestion import read_csv_records
from dhan_data_lake.models import MarketBar, ValidationError
from dhan_data_lake.quality import assess_bars


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample/market_bars.csv")
    args = parser.parse_args()
    bars = []
    invalid = 0
    for record in read_csv_records(args.input):
        try:
            bars.append(MarketBar.from_mapping(record))
        except ValidationError:
            invalid += 1
    report = assess_bars(bars)
    print(json.dumps({**asdict(report), "invalid_rows": invalid}, indent=2))
    return 0 if report.passed and invalid == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
