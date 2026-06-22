# CLI and module reference

## CLI

```text
python -m dhan_data_lake.cli --input PATH [--dry-run]
python -m dhan_data_lake.cli --input PATH --dsn DATABASE_URL [--init-db]
```

- `--dry-run` uses the in-memory repository and makes no external connection.
- `--init-db` applies the idempotent PostgreSQL migration before loading.
- Exit code `0` means at least one valid row was accepted.
- Exit code `2` means the batch contained no valid rows.

## Modules

- `models`: typed market-bar contract and record-level validation.
- `ingestion`: source readers.
- `pipeline`: validation, quarantine, deduplication, and load coordination.
- `repositories`: in-memory contract test adapter and PostgreSQL implementation.
- `quality`: dataset-level duplicate and coverage checks.
