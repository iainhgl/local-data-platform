# Deferred Work

## Deferred from: code review of 2-3-dlt-api-source-ingestion-to-bronze (2026-03-31)

- SQL injection f-string in table-name loop in `ingest/dlt_api_source.py` — pre-existing pattern in `dlt_file_source.py`; both use `f"SELECT COUNT(*) FROM bronze.{table}"` with hardcoded table names. Address holistically for both scripts.
- DuckDB verify block shares outer try/except with pipeline run in `ingest/dlt_api_source.py` — pre-existing pattern in `dlt_file_source.py`; successful pipeline run + failed DuckDB verification query produces exit code 1. Address holistically for both scripts.
