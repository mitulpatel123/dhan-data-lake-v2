# Deployment

## Local Docker deployment

1. Copy `.env.example` to `.env`.
2. Change the local database password.
3. Run `docker compose up --build --abort-on-container-exit`.
4. Rerun `docker compose run --rm loader` to verify idempotency.
5. Connect to PostgreSQL and verify four rows exist in `raw_market_bars`.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | PostgreSQL run | Connection string used by the loader |
| `DATA_INPUT_PATH` | Airflow run | Input file mounted into the worker |
| Dhan credentials | Live integration only | Must remain outside version control |

## Cloud target for the next increment

- Private PostgreSQL instance.
- Container image in a registry with vulnerability scanning.
- Scheduled task or managed Airflow worker in private networking.
- Secret manager injection rather than `.env` files.
- Central logs, failure alerts, backups, and restore tests.
- Terraform plan, cost estimate, and teardown procedure.
