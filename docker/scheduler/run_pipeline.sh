#!/bin/sh
set -e

cd /workspace

if [ ! -d /workspace/dbt_packages ]; then
  echo "ERROR: dbt_packages/ not found. Run 'make install' on the host before starting the scheduler."
  exit 1
fi

echo "▶  [cron] Running ingestion (file source)..."
PYTHONPATH=/workspace python ingest/dlt_file_source.py

echo "▶  [cron] Running ingestion (API source)..."
PYTHONPATH=/workspace python ingest/dlt_api_source.py

echo "▶  [cron] Running dbt run..."
dbt run --profiles-dir /workspace

echo "▶  [cron] Running dbt test..."
dbt test --profiles-dir /workspace

echo "▶  [cron] Generating dbt docs..."
dbt docs generate --profiles-dir /workspace

echo "✔  [cron] Pipeline complete at $(date)"
