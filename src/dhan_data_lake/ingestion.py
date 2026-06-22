"""Source readers kept separate from validation and persistence."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterator


def read_csv_records(path: str | Path) -> Iterator[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"input file not found: {source}")
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("input file must contain a header row")
        for row in reader:
            yield dict(row)
