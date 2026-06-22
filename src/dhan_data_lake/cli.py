"""Command-line entrypoint shared by local, Docker, and Airflow execution."""

from __future__ import annotations

import argparse
import json
import os

from .ingestion import read_csv_records
from .pipeline import IngestionPipeline
from .repositories import InMemoryRepository, PostgresRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest market bars safely and idempotently")
    parser.add_argument("--input", required=True, help="CSV input path")
    parser.add_argument("--dsn", default=os.getenv("DATABASE_URL", ""), help="PostgreSQL DSN")
    parser.add_argument("--init-db", action="store_true", help="Apply the database migration")
    parser.add_argument("--dry-run", action="store_true", help="Validate without external services")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        repository = InMemoryRepository()
    else:
        repository = PostgresRepository(args.dsn)
        if args.init_db:
            repository.initialize()

    report = IngestionPipeline(repository).run(read_csv_records(args.input))
    print(json.dumps(report.to_dict(), indent=2, default=str))
    return 0 if report.accepted_rows > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
