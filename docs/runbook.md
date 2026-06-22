# Operational runbook

## Loader fails to connect

1. Check `docker compose ps` and PostgreSQL health.
2. Confirm the DSN host is `postgres` inside Compose and `localhost` from the host.
3. Verify credentials match without printing passwords.
4. Retry the loader; the natural key makes reruns safe.

## Quarantine count increases

1. Query the most recent rows in `ingestion_quarantine`.
2. Group by `reason` to identify schema or source regressions.
3. Correct the provider adapter or source data.
4. Replay only the corrected records.

## dbt test fails

1. Run `dbt test --select <model>`.
2. Inspect raw natural keys and null fields.
3. Do not bypass a test by weakening it without documenting the source contract change.

## Recovery exercise

The next cloud increment must include a PostgreSQL backup, destructive test database reset, timed restore, and documented recovery time. Until that test passes, do not claim verified backup and recovery.
