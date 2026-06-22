"""Compatibility wrapper for the production-data-platform CLI."""

from dhan_data_lake.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
