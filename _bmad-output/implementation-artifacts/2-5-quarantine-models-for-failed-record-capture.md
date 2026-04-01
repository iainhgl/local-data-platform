# Story 2.5: Quarantine Models for Failed Record Capture

Status: done

## Story

As a data engineer,
I want failed records from Silver models to land in a dedicated quarantine schema with failure context,
So that pipeline failures are visible and diagnosable without hunting through logs.

## Acceptance Criteria

1. **Given** a Silver model encounters records that fail validation rules, **When** the dbt pipeline runs, **Then** rejected records land in `quarantine.faker_customers_failed`, `quarantine.faker_products_failed`, `quarantine.faker_orders_failed`, `quarantine.faker_returns_failed`; each record includes the original row data plus `_failed_reason` (varchar) and `_failed_at` (timestamp).

2. **Given** the DuckDB init runs on `make start`, **When** I inspect the DuckDB schemas, **Then** the `quarantine` schema exists before any dbt run.

3. **Given** I run `make run-pipeline` twice on clean Faker data, **When** I query `quarantine.*`, **Then** quarantine tables exist but contain zero rows (clean Faker data passes all validation rules — idempotent clean run).

## Tasks / Subtasks

- [x] Task 1: Create `models/quarantine/faker/faker_customers_failed.sql` (AC: 1, 3)
  - [x] Config: `unique_key='_dlt_id'`, `incremental_strategy='delete+insert'` (materialization inherited from `dbt_project.yml`)
  - [x] Source: `{{ source('faker_file', 'customers') }}`
  - [x] Incremental filter: `{% if is_incremental() %} WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }}) {% endif %}`
  - [x] Failed condition: `WHERE _dlt_id IS NULL OR customer_id IS NULL OR email IS NULL`
  - [x] `_failed_reason`: CASE expression identifying the first failing rule (see SQL pattern below)
  - [x] `_failed_at`: `CURRENT_TIMESTAMP`
  - [x] All original Bronze columns included
  - [x] VERIFY: `dbt run --select quarantine.faker_customers_failed` succeeds, zero rows on clean data

- [x] Task 2: Create `models/quarantine/faker/faker_products_failed.sql` (AC: 1, 3)
  - [x] Same incremental config and source pattern as faker_customers_failed
  - [x] Source: `{{ source('faker_file', 'products') }}`
  - [x] Failed condition: `WHERE _dlt_id IS NULL OR product_id IS NULL OR product_name IS NULL OR unit_price IS NULL OR unit_price <= 0`
  - [x] `_failed_reason`: CASE expression per rule
  - [x] VERIFY: `dbt run --select quarantine.faker_products_failed` succeeds, zero rows on clean data

- [x] Task 3: Create `models/quarantine/faker/faker_orders_failed.sql` (AC: 1, 3)
  - [x] Same incremental config and source pattern
  - [x] Source: `{{ source('faker_file', 'orders') }}`
  - [x] Failed condition: `WHERE _dlt_id IS NULL OR order_id IS NULL OR customer_id IS NULL OR product_id IS NULL OR quantity IS NULL OR quantity <= 0 OR total_amount IS NULL OR total_amount <= 0`
  - [x] `_failed_reason`: CASE expression per rule
  - [x] VERIFY: `dbt run --select quarantine.faker_orders_failed` succeeds, zero rows on clean data

- [x] Task 4: Create `models/quarantine/faker/faker_returns_failed.sql` (AC: 1, 3)
  - [x] Same incremental config and source pattern
  - [x] Source: `{{ source('faker_file', 'returns') }}`
  - [x] Failed condition: `WHERE _dlt_id IS NULL OR return_id IS NULL OR order_id IS NULL OR product_id IS NULL OR refund_amount IS NULL OR refund_amount <= 0`
  - [x] `_failed_reason`: CASE expression per rule
  - [x] VERIFY: `dbt run --select quarantine.faker_returns_failed` succeeds, zero rows on clean data

- [x] Task 5: Create `models/quarantine/faker/schema.yml` (AC: 1)
  - [x] Declare all four quarantine models with `description`
  - [x] Each model: at least one test — `not_null` on `_dlt_id` and `_failed_reason`
  - [x] Every column documented with `description`, `data_type`, `meta.pii: true/false`
  - [x] `_failed_reason` and `_failed_at` must be documented on every model
  - [x] VERIFY: `dbt compile --select tag:quarantine` succeeds

- [x] Task 6: Initialise `quarantine` schema before dbt runs (AC: 2)
  - [x] Check whether a DuckDB initialisation mechanism exists (Makefile, pre-hook, or script)
  - [x] Add `CREATE SCHEMA IF NOT EXISTS quarantine` to the DuckDB init path so the schema exists after `make start` and before any `dbt run`
  - [x] Simplest approach: add a `dbt run-operation` pre-step or a one-liner Python call in the Makefile's `run-pipeline` target (e.g. `python -c "import duckdb; c=duckdb.connect('dev.duckdb'); c.execute('CREATE SCHEMA IF NOT EXISTS quarantine'); c.close()"`)
  - [x] VERIFY: `duckdb dev.duckdb -c ".schema"` shows `quarantine` schema even before `dbt run`

- [x] Task 7: Remove `.gitkeep` from `models/quarantine/` (AC: 1)
  - [x] Delete `models/quarantine/.gitkeep`

- [x] Task 8: Full run verification (AC: 1, 2, 3)
  - [x] Run `dbt run --select tag:quarantine` — all four models succeed
  - [x] Verify each table has `_failed_reason` and `_failed_at` columns in schema
  - [x] Verify zero rows in all quarantine tables on clean Faker data
  - [x] Run a second time — row counts still zero (idempotency check)
  - [x] Run `dbt test --select tag:quarantine` — all tests pass

- [x] Review Follow-ups (AI)
  - [x] [AI-Review][Patch] Replace the Python one-liner in `init-duckdb` with a dbt macro and add a standalone `.env` guard.
  - [x] [AI-Review][Patch] Harden `generate_schema_name` so blank custom schemas fall back to `target.schema`.
  - [x] [AI-Review][Patch] Fix the quarantine incremental filter so an existing empty target table does not suppress future failed rows.
  - [x] [AI-Review][Patch] Remove unreachable `ELSE` branches from quarantine `_failed_reason` CASE expressions so CASE and WHERE stay exactly aligned.
  - [x] [AI-Review][Comment] Keep the `_dlt_id` `not_null` tests as implemented because Task 5 explicitly requires them; this remains a story-level tradeoff and is documented rather than silently changed.

## Dev Notes

### Quarantine Models Read from Bronze, Not Silver

Quarantine models source from `{{ source('faker_file', 'table') }}` — the same Bronze source as Silver. This ensures:
- Silver has **only clean records**
- Quarantine has **only failed records**
- Together Bronze = Silver_clean ∪ Quarantine_failed (no overlap, no loss)

Do **not** reference `{{ ref('faker_customers') }}` etc. — quarantine must not depend on Silver to avoid circular-logic failures.

### SQL Pattern (all four models follow this template)

```sql
{{ config(
    unique_key="_dlt_id",
    incremental_strategy="delete+insert"
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'customers') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})
    {% endif %}
),

failed AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        phone,
        address,
        city,
        country,
        created_at,
        _dlt_load_id,
        _dlt_id,
        CASE
            WHEN _dlt_id IS NULL THEN 'missing _dlt_id'
            WHEN customer_id IS NULL THEN 'missing customer_id'
            WHEN email IS NULL THEN 'missing email'
            ELSE 'unknown validation failure'
        END AS _failed_reason,
        'faker_customers_file' AS _source,
        CURRENT_TIMESTAMP AS _failed_at
    FROM source_data
    WHERE
        _dlt_id IS NULL
        OR customer_id IS NULL
        OR email IS NULL
)

SELECT * FROM failed
```

Key points:
- `WHERE` clause and `CASE` conditions must be **exactly consistent** — every condition in the WHERE must appear as a CASE branch
- `_failed_reason` uses CASE with priority order (most critical first)
- `_source` literal follows the same convention as Silver: `'faker_customers_file'`
- `_failed_at` is `CURRENT_TIMESTAMP` — same pattern as Silver's `_loaded_at`

### Validation Rules Per Entity

| Entity | Failed when |
|---|---|
| customers | `_dlt_id IS NULL OR customer_id IS NULL OR email IS NULL` |
| products | `_dlt_id IS NULL OR product_id IS NULL OR product_name IS NULL OR unit_price IS NULL OR unit_price <= 0` |
| orders | `_dlt_id IS NULL OR order_id IS NULL OR customer_id IS NULL OR product_id IS NULL OR quantity IS NULL OR quantity <= 0 OR total_amount IS NULL OR total_amount <= 0` |
| returns | `_dlt_id IS NULL OR return_id IS NULL OR order_id IS NULL OR product_id IS NULL OR refund_amount IS NULL OR refund_amount <= 0` |

These rules are intentionally narrow — they check structural completeness only. Broader data quality tests (FK referential integrity, domain value sets, derived field consistency) are Story 2.8.

Clean Faker data satisfies all these rules → zero rows in quarantine on every clean run (AC3).

### `dbt_project.yml` Quarantine Config

Already configured — no changes needed:
```yaml
quarantine:
  +schema: quarantine
  +materialized: incremental
  +tags: ['quarantine']
```

Do **not** add `materialized` or `tags` to model config blocks — they are inherited.

### `quarantine` Schema Initialisation

DuckDB creates schemas lazily when dbt first writes to them. For the simple profile this technically works but the AC requires the schema to exist **before** `dbt run`. The cleanest approach for Story 2.5 is to add a pre-step to `make run-pipeline` (addressed properly in Story 2.12 when the full Makefile pipeline target is built). For now, note that `dbt run --select tag:quarantine` will create the schema on first run.

If the existing `make run-pipeline` target exists and needs the schema pre-created, add a Python one-liner before the dbt command:
```bash
python -c "import duckdb; c=duckdb.connect('dev.duckdb'); c.execute('CREATE SCHEMA IF NOT EXISTS quarantine'); c.close()"
```

### Bronze Column Reference

From `models/bronze/sources.yml` — all columns available in each source table:

| Table | All columns |
|---|---|
| customers | customer_id, first_name (PII), last_name (PII), email (PII), phone (PII), address (PII), city, country, created_at, _dlt_load_id, _dlt_id |
| products | product_id, product_name, category, unit_price, sku, created_at, _dlt_load_id, _dlt_id |
| orders | order_id, customer_id, product_id, order_date, quantity, unit_price, total_amount, status, created_at, _dlt_load_id, _dlt_id |
| returns | return_id, order_id, product_id, return_date, reason, refund_amount, created_at, _dlt_load_id, _dlt_id |

### schema.yml Pattern for Quarantine

```yaml
version: 2

models:
  - name: faker_customers_failed
    description: "Records from bronze.customers that failed Silver validation rules — null customer_id, email, or _dlt_id."
    columns:
      - name: _dlt_id
        description: "dlt row-level hash (may be null for truly malformed records)"
        data_type: varchar
        meta: {pii: false}
        tests:
          - not_null
      - name: _failed_reason
        description: "Human-readable description of the first validation rule that failed"
        data_type: varchar
        meta: {pii: false}
        tests:
          - not_null
      - name: _failed_at
        description: "Timestamp when this record was written to quarantine"
        data_type: timestamp
        meta: {pii: false}
      # ... all Bronze columns with pii flags matching sources.yml
```

Note: `not_null` test on `_dlt_id` will fail for truly malformed records where `_dlt_id` itself is null. If this becomes an issue, use `_failed_reason` (always populated) as the test column instead.

### Files to Create

```
models/quarantine/faker/faker_customers_failed.sql   ← new
models/quarantine/faker/faker_products_failed.sql    ← new
models/quarantine/faker/faker_orders_failed.sql      ← new
models/quarantine/faker/faker_returns_failed.sql     ← new
models/quarantine/faker/schema.yml                   ← new
```

```
models/quarantine/.gitkeep                           ← delete
```

No Silver model files should be modified. The Makefile may need a minor pre-step addition (see Task 6).

### Scope Boundaries

- **Story 2.6 (Gold) is OUT OF SCOPE** — do not create Gold models here
- **Story 2.8 (dbt tests)** owns extended data quality tests — quarantine validation rules here are structural-completeness only
- **Story 2.12** owns the full `make run-pipeline` Makefile target — Task 6 above is a minimal pre-step only if needed for the AC2 verification

## Dev Agent Record

### Implementation Plan

- Add four incremental quarantine models that read directly from Bronze and emit failed rows with `_failed_reason`, `_failed_at`, and `_source`.
- Add a quarantine schema YAML with full column documentation and `not_null` tests on `_dlt_id` and `_failed_reason`.
- Add a DuckDB schema bootstrap hook and a schema-name macro so DuckDB materializes models into literal `silver` and `quarantine` schemas.
- Validate with targeted quarantine runs/tests, then run broader dbt and Python regression checks.

### Debug Log

- 2026-03-31: Confirmed the story file, sprint tracker, Silver model patterns, and Bronze source metadata before implementation.
- 2026-03-31: Added quarantine SQL models, schema docs/tests, and a Makefile init target; initial run showed dbt-duckdb was materializing into `main_quarantine` because no `generate_schema_name` override existed.
- 2026-03-31: Added `macros/generate_schema_name.sql` so DuckDB uses literal custom schemas; reran the quarantine models successfully into `quarantine.*`.
- 2026-03-31: Verified `make init-duckdb` creates the `quarantine` schema before any dbt run, then ran two clean quarantine dbt runs and confirmed zero-row idempotency.
- 2026-03-31: Ran `dbt test --select tag:quarantine`, `dbt build`, and `PYTHONPATH=. pytest -q tests`; all passed. Raw `pytest -q` was not used as the validation source because it collected vendored `dbt_packages/elementary` tests and missed the repo root on `PYTHONPATH`.
- 2026-03-31: Addressed review follow-ups by switching `init-duckdb` to `dbt run-operation ensure_quarantine_schema`, guarding standalone invocation with `.env`, fixing the empty-target incremental filter, removing unreachable CASE branches, and hardening `generate_schema_name` against blank custom schemas.

### Completion Notes

- Implemented all four quarantine models under `models/quarantine/faker/` with Bronze-sourced completeness filters and ordered CASE-based failure reasons.
- Added complete quarantine model documentation and tests in `models/quarantine/faker/schema.yml`, including `_failed_reason` and `_failed_at` coverage for every model.
- Added `init-duckdb` to the Makefile and a `generate_schema_name` macro so `make start` can pre-create `quarantine` and dbt materializes models into the literal `silver` and `quarantine` schemas expected by the stories.
- Verified the acceptance criteria with `make init-duckdb`, `dbt compile --select tag:quarantine`, two successful `dbt run --select tag:quarantine` executions, zero-row checks on all four quarantine tables, `dbt test --select tag:quarantine`, `dbt build`, and `PYTHONPATH=. pytest -q tests`.
- Addressed the actionable review findings without widening scope: removed shell-interpolated Python from the Makefile, added a dedicated schema-init macro, fixed the incremental NULL edge case, removed dead CASE branches, and tightened schema-name fallback behavior.
- Left the `_dlt_id` `not_null` tests in place as an explicit documented comment because Task 5 requires them verbatim; changing that behavior would contradict the story instructions rather than implement the review literally.

## File List

- Makefile
- macros/ensure_quarantine_schema.sql
- macros/generate_schema_name.sql
- models/quarantine/faker/faker_customers_failed.sql
- models/quarantine/faker/faker_products_failed.sql
- models/quarantine/faker/faker_orders_failed.sql
- models/quarantine/faker/faker_returns_failed.sql
- models/quarantine/faker/schema.yml
- models/quarantine/.gitkeep

## Change Log

- 2026-03-31: Implemented quarantine failed-record models, added quarantine schema initialization, documented/tested the new models, and aligned dbt schema routing to literal schema names for DuckDB.
- 2026-03-31: Addressed post-review fixes for schema initialization safety, empty-target incremental behavior, CASE alignment, and schema-name fallback handling; documented the `_dlt_id` test tradeoff.

## Review Findings (Pass 1 — resolved)

All pass-1 patch findings were addressed by the implementor. See "Review Follow-ups (AI)" above.

## Review Findings (Pass 2)

### Patch

- [x] [Review][Patch] `ensure_quarantine_schema` has no adapter guard — `run_query` fires against whatever dbt profile is currently active; on a postgres or lakehouse profile this creates a `quarantine` schema in the wrong database unexpectedly; add `{% if target.type == 'duckdb' %}` guard [macros/ensure_quarantine_schema.sql]

### Defer

- [x] [Review][Defer] `dbt run-operation` in `init-duckdb` assumes dbt installed and `dbt deps` run — project-wide assumption shared by all other dbt Makefile targets; not introduced by this change [Makefile] — deferred, pre-existing project-wide requirement
- [x] [Review][Defer] CASE/WHERE future maintenance divergence — pattern is by design per spec; adding a rule to one without the other would produce NULL `_failed_reason`; Story 2.8 tests will surface divergence [all 4 quarantine models] — deferred, acceptable risk for structural-completeness-only quarantine
- [x] [Review][Defer] `_dlt_load_id` lexicographic sort risk — varchar > comparison is lexicographic not numeric; works in practice for dlt Unix timestamp strings but fragile if format changes [all 4 quarantine models] — deferred, pre-existing Silver model pattern
- [x] [Review][Defer] NULL `_dlt_id` deduplication limitation — `delete+insert` on `unique_key='_dlt_id'` cannot deduplicate NULL-keyed rows across runs [all 4 quarantine models] — deferred, inherent to spec-mandated design
- [x] [Review][Defer] `init-duckdb` runs unconditionally on every `make start` — idempotent; acceptable overhead for a local dev tool [Makefile] — deferred, by design
