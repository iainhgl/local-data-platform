# Story 2.4: Silver Layer dbt Models with Medallion Structure

Status: done

## Story

As a data engineer,
I want dbt Silver models that read from Bronze, clean and deduplicate records, and add transformation metadata,
So that a clean, consistent representation of each entity is available for Gold layer consumption.

## Acceptance Criteria

1. **Given** Bronze tables are populated, **When** I run `dbt run --select tag:silver`, **Then** four Silver models materialise: `silver.faker_orders`, `silver.faker_customers`, `silver.faker_products`, `silver.faker_returns`.

2. **Given** a Silver model runs, **When** I inspect the resulting table schema, **Then** `_dlt_load_id`, `_dlt_id`, `_loaded_at` (CURRENT_TIMESTAMP), and `_source` (string literal) are present on every Silver table; all column names are `snake_case`; all timestamp columns use `TIMESTAMP` type (not VARCHAR or epoch).

3. **Given** I run `dbt run --select tag:silver` twice on the same Bronze data, **When** I count Silver rows after each run, **Then** row counts are identical — incremental `delete+insert` strategy using `_dlt_id` as unique key.

4. **Given** a Silver model file, **When** I inspect the SQL, **Then** the model uses CTEs exclusively (no inline subqueries), and `{{ source('faker_file', 'table') }}` is used — no hardcoded `bronze.table` references.

5. **Given** the Silver `schema.yml`, **When** I inspect it, **Then** every model has a `description`, at least one test, and every column has `description`, `data_type`, and `meta.pii: true/false`.

## Tasks / Subtasks

- [x] Task 1: Create `models/silver/faker/faker_customers.sql` (AC: 1, 2, 3, 4)
  - [x] Use `{{ config(unique_key='_dlt_id', incremental_strategy='delete+insert') }}` block (inherited materialization from `dbt_project.yml`, only unique_key and strategy needed)
  - [x] CTE `source_data` selects from `{{ source('faker_file', 'customers') }}`
  - [x] CTE `deduplicated` partitions by `_dlt_id` to deduplicate, selects latest record using `_dlt_load_id DESC`
  - [x] Final SELECT projects all columns, adding `CURRENT_TIMESTAMP AS _loaded_at` and `'faker_customers_file' AS _source`
  - [x] All original Bronze columns included: `customer_id`, `first_name`, `last_name`, `email`, `phone`, `address`, `city`, `country`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [x] Incremental filter: `{% if is_incremental() %} WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }}) {% endif %}`
  - [x] VERIFY: `dbt run --select silver.faker_customers` succeeds

- [x] Task 2: Create `models/silver/faker/faker_products.sql` (AC: 1, 2, 3, 4)
  - [x] Same CTE + incremental pattern as `faker_customers`
  - [x] Source: `{{ source('faker_file', 'products') }}`
  - [x] `_source` literal: `'faker_products_file'`
  - [x] All Bronze columns: `product_id`, `product_name`, `category`, `unit_price`, `sku`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [x] VERIFY: `dbt run --select silver.faker_products` succeeds

- [x] Task 3: Create `models/silver/faker/faker_orders.sql` (AC: 1, 2, 3, 4)
  - [x] Same CTE + incremental pattern as `faker_customers`
  - [x] Source: `{{ source('faker_file', 'orders') }}`
  - [x] `_source` literal: `'faker_orders_file'`
  - [x] All Bronze columns: `order_id`, `customer_id`, `product_id`, `order_date`, `quantity`, `unit_price`, `total_amount`, `status`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [x] VERIFY: `dbt run --select silver.faker_orders` succeeds

- [x] Task 4: Create `models/silver/faker/faker_returns.sql` (AC: 1, 2, 3, 4)
  - [x] Same CTE + incremental pattern as `faker_customers`
  - [x] Source: `{{ source('faker_file', 'returns') }}`
  - [x] `_source` literal: `'faker_returns_file'`
  - [x] All Bronze columns: `return_id`, `order_id`, `product_id`, `return_date`, `reason`, `refund_amount`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [x] VERIFY: `dbt run --select silver.faker_returns` succeeds

- [x] Task 5: Create `models/silver/faker/schema.yml` (AC: 5)
  - [x] Declare all four models with `description`
  - [x] Each model: at least one test (e.g. `unique` + `not_null` on the business primary key)
  - [x] Every column documented with `description`, `data_type`, `meta: {pii: true/false}`
  - [x] Columns `_loaded_at` and `_source` documented for each model
  - [x] VERIFY: `dbt compile` succeeds; `yamllint models/silver/faker/schema.yml` passes

- [x] Task 6: Remove `.gitkeep` from `models/silver/` (AC: 1)
  - [x] Delete `models/silver/.gitkeep` — it was a placeholder; replace with real files

- [x] Task 7: Full run and idempotency verification (AC: 1, 2, 3)
  - [x] Ensure Bronze is populated: `python ingest/dlt_file_source.py`
  - [x] Run: `dbt run --select tag:silver` — all four models succeed
  - [x] Inspect schema: confirm `_loaded_at` and `_source` present on each Silver table
  - [x] Run again: `dbt run --select tag:silver` — row counts unchanged (idempotency)
  - [x] Run: `dbt test --select tag:silver` — all tests pass

### Review Findings

- [x] [Review][Defer] `_dlt_load_id` varchar comparison in incremental filter and deduplication window [`models/silver/faker/*.sql`] — deferred; `_dlt_load_id` is a varchar holding decimal Unix timestamp strings (e.g. `"1712345678.123456"`); lexicographic comparison is numerically correct for current dlt format but is not guaranteed. `ORDER BY _dlt_load_id DESC` in the dedup window has the same assumption. Address holistically across all Silver models when data quality patterns are established in Story 2.8.
- [x] [Review][Defer] `delete+insert` strategy does not propagate Bronze hard-deletes to Silver [`models/silver/faker/*.sql`] — deferred; known limitation of the `delete+insert` incremental strategy — rows deleted from Bronze are not removed from Silver. Intentional: Bronze is append-only by dlt design. Document as known behaviour.
- [x] [Review][Defer] Missing data quality tests: `total_amount` vs `quantity * unit_price`, FK relationship tests on `faker_returns`, `not_null` on FK columns, `unit_price` non-negative constraint [`models/silver/faker/schema.yml`] — deferred; all data quality and relationship tests belong in Story 2.8 (dbt tests, dbt-expectations).
- [x] [Review][Defer] `CURRENT_TIMESTAMP` returns different types across DuckDB / Postgres / Trino — `TIMESTAMP WITH TIME ZONE` vs `TIMESTAMP(3) WITH TIME ZONE`; `schema.yml` declares `data_type: timestamp` [`models/silver/faker/*.sql`] — deferred; no impact on current simple (DuckDB) profile. Revisit when Postgres and Trino profiles are implemented in Stories 3–4.
- [x] [Review][Defer] `meta.pii: true` flags in `schema.yml` are advisory only — no masking applied at the Silver model level [`models/silver/faker/schema.yml`] — deferred; PII masking is out of scope for Story 2.4. Addressed in Story 3.2 (three-role RBAC and PII column masking).

## Dev Notes

### Critical: Source Name is `faker_file`, NOT `faker`

The epics document says `{{ source('faker', 'table') }}` but **this is wrong**. The actual registered source in `models/bronze/sources.yml` is:

```yaml
sources:
  - name: faker_file   # ← THIS is the source name
    schema: bronze
    tables:
      - name: customers
      - name: products
      - name: orders
      - name: returns
```

**Always use `{{ source('faker_file', 'customers') }}`** etc. Using `source('faker', ...)` will cause `dbt compile` to fail with "source faker not found".

### Model File Location

All four models go in `models/silver/faker/` — the `faker/` subdirectory groups Faker-sourced Silver models together. The `dbt_project.yml` Silver config applies to the whole `silver/` directory tree:

```yaml
models:
  local_data_platform:
    silver:
      +schema: silver
      +materialized: incremental
      +tags: ['silver']
```

Do **not** add `{{ config(materialized='incremental') }}` in the model file — it's inherited. Only add `unique_key` and `incremental_strategy`.

### Incremental Config Pattern

```sql
{{ config(
    unique_key='_dlt_id',
    incremental_strategy='delete+insert'
) }}
```

The `delete+insert` strategy works across DuckDB, Postgres, and Trino. The `_dlt_id` is the dlt-generated row-level hash — it is stable across re-runs for the same source row, making it the correct deduplication key.

### CTE Pattern (all four models follow this template)

```sql
{{ config(
    unique_key='_dlt_id',
    incremental_strategy='delete+insert'
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'customers') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY _dlt_id ORDER BY _dlt_load_id DESC) AS _row_num
    FROM source_data
),

final AS (
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
        CURRENT_TIMESTAMP AS _loaded_at,
        'faker_customers_file' AS _source
    FROM deduplicated
    WHERE _row_num = 1
)

SELECT * FROM final
```

Adapt column list per entity. The `_row_num = 1` filter after `ROW_NUMBER()` is the deduplication step.

### Bronze Column Reference

From `models/bronze/sources.yml`:

| Table | Business PK | Columns |
|---|---|---|
| `customers` | `customer_id` | customer_id, first_name (PII), last_name (PII), email (PII), phone (PII), address (PII), city, country, created_at, _dlt_load_id, _dlt_id |
| `products` | `product_id` | product_id, product_name, category, unit_price, sku, created_at, _dlt_load_id, _dlt_id |
| `orders` | `order_id` | order_id, customer_id, product_id, order_date, quantity, unit_price, total_amount, status, created_at, _dlt_load_id, _dlt_id |
| `returns` | `return_id` | return_id, order_id, product_id, return_date, reason, refund_amount, created_at, _dlt_load_id, _dlt_id |

### `schema.yml` Pattern

```yaml
version: 2

models:
  - name: faker_customers
    description: "Cleaned and deduplicated customer records from Faker bronze source"
    config:
      tags: ['silver']
    columns:
      - name: customer_id
        description: "UUID primary key"
        data_type: varchar
        meta: {pii: false}
        tests:
          - unique
          - not_null
      - name: first_name
        description: "Customer first name — PII"
        data_type: varchar
        meta: {pii: true}
      - name: last_name
        description: "Customer last name — PII"
        data_type: varchar
        meta: {pii: true}
      - name: email
        description: "Customer email address — PII"
        data_type: varchar
        meta: {pii: true}
      - name: phone
        description: "Customer phone number — PII"
        data_type: varchar
        meta: {pii: true}
      - name: address
        description: "Street address — PII"
        data_type: varchar
        meta: {pii: true}
      - name: city
        description: "City name"
        data_type: varchar
        meta: {pii: false}
      - name: country
        description: "2-letter ISO country code"
        data_type: varchar
        meta: {pii: false}
      - name: created_at
        description: "Record creation timestamp from source system"
        data_type: timestamp
        meta: {pii: false}
      - name: _dlt_load_id
        description: "dlt load batch identifier — inherited from Bronze"
        data_type: varchar
        meta: {pii: false}
      - name: _dlt_id
        description: "dlt row-level hash — unique key used for incremental deduplication"
        data_type: varchar
        meta: {pii: false}
        tests:
          - unique
          - not_null
      - name: _loaded_at
        description: "Timestamp when Silver model ran"
        data_type: timestamp
        meta: {pii: false}
      - name: _source
        description: "Source system identifier: 'faker_customers_file'"
        data_type: varchar
        meta: {pii: false}
```

Repeat for the other three models with their respective columns and `_source` literal values.

### Scope Boundaries

- **Story 2.5 (Quarantine) is OUT OF SCOPE.** Do not create `quarantine.*_failed` models in this story — that is Story 2.5.
- **jsonplaceholder data** (`bronze.posts`, `bronze.users`) is NOT referenced by any Silver model. Silver reads only from the `faker_file` source.
- Do not create Gold models — that is Story 2.6.

### Previous Story Patterns

From Story 2.3 review: always use `load_info.raise_on_failed_jobs()` pattern in ingest scripts. This is not relevant to dbt models but is relevant context for the pipeline as a whole.

The `ingest/__init__.py` was created in Story 2.3 to make `ingest/` a Python package — no changes needed there.

### Test Execution

Run tests with:
```bash
# Compile only (fast check)
dbt compile --select tag:silver

# Full run
dbt run --select tag:silver

# Tests
dbt test --select tag:silver
```

No pytest tests are expected for this story — dbt schema tests in `schema.yml` are the test suite for Silver models.

### Files to Create

```
models/silver/faker/faker_customers.sql   ← new
models/silver/faker/faker_orders.sql      ← new
models/silver/faker/faker_products.sql    ← new
models/silver/faker/faker_returns.sql     ← new
models/silver/faker/schema.yml            ← new
```

```
models/silver/.gitkeep                    ← delete (replaced by real files)
```

No other files should be modified.

## Dev Agent Record

### Agent Model Used

Codex GPT-5

### Implementation Plan

- Mark Story 2.4 as in progress in sprint tracking, then implement the four Silver models in the exact task order from the story.
- Add the Silver `schema.yml` with model/column metadata and schema tests aligned to the Bronze source definitions.
- Remove the Silver placeholder, run dbt compile/run/test plus idempotency checks, and only then update task checkboxes, file list, change log, and status.

### Debug Log References

- `python3 ingest/dlt_file_source.py`
- `dbt compile --profiles-dir . --select tag:silver`
- `dbt ls --profiles-dir . --resource-type model --select faker_customers`
- `dbt run --profiles-dir . --select faker_customers`
- `dbt run --profiles-dir . --select faker_products`
- `dbt run --profiles-dir . --select faker_orders`
- `dbt run --profiles-dir . --select faker_returns`
- `dbt run --profiles-dir . --select tag:silver`
- `python3 -m yamllint models/silver/faker/schema.yml`
- `python3 -c "import duckdb; ..."` (schema and row-count verification against `main_silver.*`)
- `dbt test --profiles-dir . --select tag:silver`

### Completion Notes List

- Implemented four Silver incremental dbt models under `models/silver/faker/`, each using the required CTE-only pattern, `delete+insert` incremental strategy, `_dlt_id` unique key, deduplication by latest `_dlt_load_id`, and `_loaded_at` / `_source` metadata columns.
- Added `models/silver/faker/schema.yml` documenting every model and column with `description`, `data_type`, and `meta.pii`, plus `unique` and `not_null` schema tests on each business primary key and `_dlt_id`.
- Removed `models/silver/.gitkeep` and replaced the placeholder directory with real Silver models.
- Validated compile, per-model runs, full `tag:silver` runs, YAML lint, and dbt tests successfully.
- Verified idempotency after two consecutive `dbt run --select tag:silver` executions with stable row counts: customers=1000, products=1000, orders=1000, returns=609.
- Verified Silver metadata columns exist on every table and resolve to the dbt-created `main_silver` schema in DuckDB (`_dlt_load_id`, `_dlt_id`, `_loaded_at`, `_source`).
- Noted two environment-specific details during validation: dbt model selectors in this project resolve by model name/FQN rather than `silver.<model>`, and DuckDB single-writer locking requires sequential local `dbt run` commands when targeting the same file.

### File List

- `models/silver/faker/faker_customers.sql` (created)
- `models/silver/faker/faker_products.sql` (created)
- `models/silver/faker/faker_orders.sql` (created)
- `models/silver/faker/faker_returns.sql` (created)
- `models/silver/faker/schema.yml` (created)
- `models/silver/.gitkeep` (deleted)

## Change Log

- 2026-03-31: Story 2.4 started — Silver layer dbt model implementation in progress.
- 2026-03-31: Implemented Faker Silver dbt models, added Silver schema documentation/tests, removed the Silver placeholder, and validated compile, runs, idempotency, and dbt tests. Status → review.
