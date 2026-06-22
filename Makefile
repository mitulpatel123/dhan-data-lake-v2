.PHONY: test dry-run compose-check up dbt

test:
	python -m compileall -q src tests
	python -m pytest -q

dry-run:
	python -m dhan_data_lake.cli --input data/sample/market_bars.csv --dry-run

compose-check:
	docker compose config

up:
	docker compose up --build --abort-on-container-exit

dbt:
	cd analytics && dbt build
