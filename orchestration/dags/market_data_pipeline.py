"""Airflow DAG for the tested batch-ingestion entrypoint."""

from __future__ import annotations

from datetime import datetime
import os

from airflow import DAG
from airflow.operators.bash import BashOperator


with DAG(
    dag_id="dhan_market_data_ingestion",
    description="Validate, quarantine, and idempotently load market bars",
    start_date=datetime(2026, 1, 1),
    schedule="0 18 * * 1-5",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2},
    tags=["portfolio", "data-engineering"],
) as dag:
    ingest = BashOperator(
        task_id="ingest_market_bars",
        bash_command=(
            "python -m dhan_data_lake.cli "
            "--input '${DATA_INPUT_PATH}' --dsn '${DATABASE_URL}' --init-db"
        ),
        env={
            "DATA_INPUT_PATH": os.environ["DATA_INPUT_PATH"],
            "DATABASE_URL": os.environ["DATABASE_URL"],
        },
        append_env=True,
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/airflow/dhan-data-lake-v2/analytics && dbt build",
    )

    ingest >> dbt_build
