# Deferred Work

## Deferred from: code review of 2-6-gold-layer-facts-dimensions-and-marts (2026-04-01)

- Silver incremental `_dlt_load_id` watermark non-monotonic — pre-existing pattern in all Silver models; late-arriving or backfilled batches with a lower load_id than current max are silently skipped forever; address holistically when Silver models are revisited
- `_source` literal hardcoded with no `accepted_values` test across all Gold models — Story 2.8 owns extended data quality test coverage
- `ensure_quarantine_schema` silently no-ops for non-duckdb-derived target types (e.g. motherduck adapter) — acceptable for local dev tool; revisit when multi-profile support is added
- `init-duckdb` success echo prints even if dbt skips schema creation due to target type mismatch — make exits non-zero on actual dbt failure; acceptable for local dev tool

## Deferred from: code review of 2-5-quarantine-models-for-failed-record-capture pass 2 (2026-04-01)

- `ensure_quarantine_schema` adapter guard — deferred to confirm non-DuckDB profiles are in scope; add `{% if target.type == 'duckdb' %}` guard when multi-profile support is tested
- `dbt run-operation` in `init-duckdb` assumes dbt installed/deps run — project-wide assumption; document in README or add a pre-flight check target
- CASE/WHERE future maintenance divergence — acceptable for now; Story 2.8 dbt tests will surface any future drift
- `_dlt_load_id` lexicographic sort — pre-existing Silver pattern; address holistically when Silver models are revisited
- NULL `_dlt_id` deduplication limitation — inherent to spec design; acceptable for structural-completeness quarantine

## Deferred from: code review of 2-5-quarantine-models-for-failed-record-capture (2026-03-31)

- `init-duckdb` runs unconditionally on every `make start` — idempotent; acceptable overhead for a local dev tool
- Timezone-naive `_failed_at` (CURRENT_TIMESTAMP) — project-wide convention matching Silver's `_loaded_at`; address holistically
- No extended model-level tests (accepted_values, row-count) — Story 2.8 owns extended data quality test coverage
- NULL _dlt_id rows accumulate across incremental runs — unique_key delete+insert cannot deduplicate NULL keys; inherent spec design limitation; acceptable for structural-completeness-only quarantine
- `_dlt_load_id` lexicographic sort — varchar > comparison works for dlt Unix timestamp strings but fragile; pre-existing Silver model pattern; address holistically

## Deferred from: code review of 2-3-dlt-api-source-ingestion-to-bronze (2026-03-31)

- SQL injection f-string in table-name loop in `ingest/dlt_api_source.py` — pre-existing pattern in `dlt_file_source.py`; both use `f"SELECT COUNT(*) FROM bronze.{table}"` with hardcoded table names. Address holistically for both scripts.
- DuckDB verify block shares outer try/except with pipeline run in `ingest/dlt_api_source.py` — pre-existing pattern in `dlt_file_source.py`; successful pipeline run + failed DuckDB verification query produces exit code 1. Address holistically for both scripts.

## Deferred from: code review of 2-4-silver-layer-dbt-models-with-medallion-structure (2026-03-31)

- `_dlt_load_id` varchar comparison in incremental filter and deduplication window — `models/silver/faker/*.sql`; all four models use `WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})` and `ORDER BY _dlt_load_id DESC` with varchar; lexicographic ordering matches numeric ordering for current dlt decimal-string format but is not guaranteed. Address holistically across all Silver models in Story 2.8.
- `delete+insert` does not propagate Bronze hard-deletes to Silver — `models/silver/faker/*.sql`; known strategy limitation; Bronze is append-only so this is intentional. Document as known behaviour.
- Missing data quality tests: `total_amount` integrity (`quantity * unit_price`), FK relationship tests on `faker_returns`, `not_null` on FK columns in `faker_orders`/`faker_returns`, `unit_price` non-negative constraint — `models/silver/faker/schema.yml`; address in Story 2.8 (dbt tests and dbt-expectations).
- `CURRENT_TIMESTAMP` type mismatch across engines — DuckDB/Postgres return `TIMESTAMP WITH TIME ZONE`, Trino returns `TIMESTAMP(3) WITH TIME ZONE`; `schema.yml` declares `data_type: timestamp`. No impact on simple profile. Revisit in Stories 3–4.
- `meta.pii: true` flags are advisory only — no masking applied at Silver model level — `models/silver/faker/schema.yml`; masking addressed in Story 3.2.
