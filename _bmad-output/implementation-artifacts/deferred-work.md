# Deferred Work

## Deferred from: code review of 3-2-three-role-rbac-and-pii-column-masking (2026-04-14)

- `pii_access_log` never auto-populated — no trigger/pgAudit/function inserts rows; `pg-show-pii-log` always returns zero rows; dev notes explicitly defer automatic logging to Story 5.x
- Masking not applied under `full` profile — Makefile guard is `COMPOSE_PROFILES=postgres` exact match; `full` profile uses Postgres too but skips masking; out of scope until Epic 5
- No transaction wrapper in `postgres_masking.sql` — partial `dbt run` failure leaves some views created and some not with no rollback; acceptable for local dev usage pattern
- `ALTER SYSTEM SET log_statement = 'all'` is server-wide — all databases and users on the instance; intentional for this local dev platform per dev notes
- Column order mismatch in `silver.faker_customers_masked` — view emits `_source, _loaded_at` in swapped order relative to `schema.yml`; cosmetic, no functional impact
- Tests don't verify per-view PII coverage — `test_masking_sql_redacts_expected_pii_columns` passes if each PII column redaction appears anywhere in the file; weak coverage of per-view correctness

## Deferred from: code review of 3-1-postgres-profile-docker-compose-and-dbt-adapter (2026-04-14)

- `ALTER DEFAULT PRIVILEGES` scope limited to init-script executor role — correct today (dlt/dbt run as `POSTGRES_USER`/dbt); latent RBAC gap if future roles diverge; revisit in Story 3.2
- SQL identifier interpolation in `_verify_counts()` — f-strings used for table names against psycopg2; low risk while ENTITIES/TABLES are constants but should use `psycopg2.sql.Identifier`; pre-existing pattern also noted in Story 2.3 deferred work
- `COMPOSE_PROFILES` read at module-level import time — makes postgres branch untestable without process isolation; runtime behavior correct via Makefile; address when ingest scripts are refactored
- No runtime integration tests — AC 1/2 are behavioral but all tests are structural (file-content assertions); acceptable for local dev tool, revisit when container-level CI is added
- `make start` calls `init-duckdb` unconditionally regardless of profile — pre-existing issue; `init-duckdb` targets DuckDB and may misbehave on `postgres` profile; address when `start` target is made profile-aware
- `lakehouse` profile falls into `run-pipeline` `else` branch with DuckDB-specific skip message — misleading for Trino; fix when lakehouse profile is implemented in Epic 4
- `_verify_counts` asymmetric signatures between `dlt_file_source.py` (no args) and `dlt_api_source.py` (duckdb_path arg) — minor inconsistency; fix when ingest scripts are refactored holistically
- Empty `POSTGRES_PASSWORD` default in `_get_destination()` emits no warning — acceptable for local dev; `.env.example` documents intended value
- Test backslash continuation assertion fragility in `test_story_3_1_postgres_profile.py` — tests Makefile formatting, not behavior; low impact

## Deferred from: code review of 2-14-cron-schedule-and-readme (2026-04-10)

- DuckDB write-lock race condition: if host `make run-pipeline` runs concurrently with the cron-scheduler container, the second opener receives `IOException: Could not set lock on file`; pre-existing for all concurrent dbt access; documented in story Dev Notes; address if parallel execution is required
- Pipeline fires immediately on `cron-scheduler` container start before the first `CRON_INTERVAL` elapses — intentional UX choice for a learning tool; revisit if users find the immediate first run unexpected
- `restart: unless-stopped` + `set -e` in `run_pipeline.sh` causes tight crash-restart loop on any pipeline failure — pre-existing pattern shared by Elementary and Evidence services; add `restart: on-failure` with `max_retries` if restart storms become a problem in practice
- No version pins in `docker/scheduler/Dockerfile` — pre-existing project convention; requirements.txt also unpinned; pin once the image is considered stable for a production-like workflow

## Deferred from: code review of 2-13-dbt-documentation-and-column-lineage (2026-04-10)

- `run-pipeline` does not assert Docker services are running before opening docs — pre-existing UX pattern; `make start` is the documented prerequisite; no change required unless README is updated to add an explicit service-up step
- Port `18020` (and all other services) bind on all host interfaces (`0.0.0.0`) — pre-existing across all services; local dev tool by design; restrict bind address if multi-user or CI network exposure becomes a concern
- DuckDB exclusive write-lock causes failures if `make run-pipeline` runs in parallel — pre-existing across all dbt commands; no serialisation exists in any Makefile target; address if parallel CI pipelines are introduced
- No atomic swap for `target/catalog.json` on pipeline re-run — partially written file briefly served by the dbt-docs container while pipeline regenerates; pre-existing pattern shared by Elementary and Evidence services

## Deferred from: code review of 2-11-evidence-analytical-reports (2026-04-08)

- Dual Evidence plugin config files (`evidence.plugins.yaml` + `evidence.config.yaml`) with different key formats — scaffold generates `evidence.config.yaml` (newer `datasources:` format); investigate whether `evidence.plugins.yaml` is still read by Evidence v40 or can be removed
- Evidence container starts before pipeline has run — no `depends_on` in docker-compose; Evidence shows empty data on first start; acceptable for local dev workflow but could be improved with a startup ordering note in README
- `package.json` includes 12 unused connector dependencies from template scaffold — bloats npm install time; consider trimming to only `@evidence-dev/duckdb` and core packages in a future story

## Deferred from: code review of 2-9-elementary-observability-dashboard (2026-04-08)

- `open-docs` target opens `http://localhost:18030/` (directory listing) not `/elementary_report.html` directly — minor UX issue; could update `open-docs` URL to `/elementary_report.html` or add an `index.html` redirect inside the container
- No post-run validation that `edr_target/elementary_report.html` was generated — Makefile could add a `test -f edr_target/elementary_report.html` guard after `edr report`; consistent with project pattern of not validating outputs

## Deferred from: code review of 2-8-dbt-tests-dbt-expectations-and-source-freshness (2026-04-01)

- `order_date` and `return_date` have no `not_null` or temporal range tests — FK columns guarded in this story but temporal keys remain uncovered across faker_orders and faker_returns; address when Silver model coverage is expanded
- No upper-bound tests on `quantity`, `unit_price`, or `total_amount` — extreme outliers from Faker or data corruption pass silently; add max_value bounds when numeric test coverage is revisited

## Deferred from: code review of 2-12-make-run-pipeline-and-make-open-docs-commands (2026-04-01)

- `_target_block` parser in `tests/test_makefile_targets.py` terminates block collection on any blank line — a blank line within a Make recipe body (valid syntax) would silently return a truncated block; not triggered by current Makefile but fragile
- Tests in `tests/test_makefile_targets.py` verify Makefile text content, not runtime execution — ingest scripts, dbt, and browser-open are not exercised; design choice for this unit-level test but provides no runtime confidence
- Ingest scripts (`ingest/dlt_file_source.py`, `ingest/dlt_api_source.py`) may exit 0 even on partial pipeline failure — Make would continue to `dbt run` against incomplete Bronze data; address when ingest script error handling is revisited holistically
- `PYTHONPATH=.` in `run-pipeline` clobbers any pre-existing `PYTHONPATH` in the caller environment — `PYTHONPATH=.:$(PYTHONPATH)` would be safer for CI environments; consistent with established project pattern

## Deferred from: story 2-12 validation (2026-04-01)

- Second `make run-pipeline` run fails uniqueness tests across Silver and Gold models (`faker_customers.customer_id`, `faker_products.product_id`, `faker_orders.order_id`, `faker_returns.return_id`, `dim_customers.customer_id`, `dim_products.product_id`, `fct_orders.order_id`, `orders_mart.order_id`) even after the orphaned `jaffle_shop_*` seed scaffold is removed. This should be treated as the concrete rerun symptom of the pre-existing Silver incremental `_dlt_load_id` deferred work from Story 2.4, not as a new isolated Makefile issue. Trace back to: "Deferred from: code review of 2-4-silver-layer-dbt-models-with-medallion-structure (2026-03-31)" and the related Silver `_dlt_load_id` watermark / ordering bullets below.

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
