FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

COPY sql ./sql
COPY data/sample ./data/sample

ENTRYPOINT ["python", "-m", "dhan_data_lake.cli"]
CMD ["--input", "/app/data/sample/market_bars.csv", "--init-db"]
