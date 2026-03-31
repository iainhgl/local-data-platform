# Deferred Work

## Deferred from: code review of 2-3-dlt-api-source-ingestion-to-bronze (2026-03-31)

- SQL injection f-string in table-name loop in `ingest/dlt_api_source.py` — pre-existing pattern in `dlt_file_source.py`; both use `f"SELECT COUNT(*) FROM bronze.{table}"` with hardcoded table names. Address holistically for both scripts.
- DuckDB verify block shares outer try/except with pipeline run in `ingest/dlt_api_source.py` — pre-existing pattern in `dlt_file_source.py`; successful pipeline run + failed DuckDB verification query produces exit code 1. Address holistically for both scripts.

## Deferred from: code review of 2-4-silver-layer-dbt-models-with-medallion-structure (2026-03-31)

- `_dlt_load_id` varchar comparison in incremental filter and deduplication window — `models/silver/faker/*.sql`; all four models use `WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})` and `ORDER BY _dlt_load_id DESC` with varchar; lexicographic ordering matches numeric ordering for current dlt decimal-string format but is not guaranteed. Address holistically across all Silver models in Story 2.8.
- `delete+insert` does not propagate Bronze hard-deletes to Silver — `models/silver/faker/*.sql`; known strategy limitation; Bronze is append-only so this is intentional. Document as known behaviour.
- Missing data quality tests: `total_amount` integrity (`quantity * unit_price`), FK relationship tests on `faker_returns`, `not_null` on FK columns in `faker_orders`/`faker_returns`, `unit_price` non-negative constraint — `models/silver/faker/schema.yml`; address in Story 2.8 (dbt tests and dbt-expectations).
- `CURRENT_TIMESTAMP` type mismatch across engines — DuckDB/Postgres return `TIMESTAMP WITH TIME ZONE`, Trino returns `TIMESTAMP(3) WITH TIME ZONE`; `schema.yml` declares `data_type: timestamp`. No impact on simple profile. Revisit in Stories 3–4.
- `meta.pii: true` flags are advisory only — no masking applied at Silver model level — `models/silver/faker/schema.yml`; masking addressed in Story 3.2.
