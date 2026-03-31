# Story 2.4: Silver Layer dbt Models with Medallion Structure

Status: ready-for-dev

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

- [ ] Task 1: Create `models/silver/faker/faker_customers.sql` (AC: 1, 2, 3, 4)
  - [ ] Use `{{ config(unique_key='_dlt_id', incremental_strategy='delete+insert') }}` block (inherited materialization from `dbt_project.yml`, only unique_key and strategy needed)
  - [ ] CTE `source_data` selects from `{{ source('faker_file', 'customers') }}`
  - [ ] CTE `deduplicated` partitions by `_dlt_id` to deduplicate, selects latest record using `_dlt_load_id DESC`
  - [ ] Final SELECT projects all columns, adding `CURRENT_TIMESTAMP AS _loaded_at` and `'faker_customers_file' AS _source`
  - [ ] All original Bronze columns included: `customer_id`, `first_name`, `last_name`, `email`, `phone`, `address`, `city`, `country`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [ ] Incremental filter: `{% if is_incremental() %} WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }}) {% endif %}`
  - [ ] VERIFY: `dbt run --select silver.faker_customers` succeeds

- [ ] Task 2: Create `models/silver/faker/faker_products.sql` (AC: 1, 2, 3, 4)
  - [ ] Same CTE + incremental pattern as `faker_customers`
  - [ ] Source: `{{ source('faker_file', 'products') }}`
  - [ ] `_source` literal: `'faker_products_file'`
  - [ ] All Bronze columns: `product_id`, `product_name`, `category`, `unit_price`, `sku`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [ ] VERIFY: `dbt run --select silver.faker_products` succeeds

- [ ] Task 3: Create `models/silver/faker/faker_orders.sql` (AC: 1, 2, 3, 4)
  - [ ] Same CTE + incremental pattern as `faker_customers`
  - [ ] Source: `{{ source('faker_file', 'orders') }}`
  - [ ] `_source` literal: `'faker_orders_file'`
  - [ ] All Bronze columns: `order_id`, `customer_id`, `product_id`, `order_date`, `quantity`, `unit_price`, `total_amount`, `status`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [ ] VERIFY: `dbt run --select silver.faker_orders` succeeds

- [ ] Task 4: Create `models/silver/faker/faker_returns.sql` (AC: 1, 2, 3, 4)
  - [ ] Same CTE + incremental pattern as `faker_customers`
  - [ ] Source: `{{ source('faker_file', 'returns') }}`
  - [ ] `_source` literal: `'faker_returns_file'`
  - [ ] All Bronze columns: `return_id`, `order_id`, `product_id`, `return_date`, `reason`, `refund_amount`, `created_at`, `_dlt_load_id`, `_dlt_id`
  - [ ] VERIFY: `dbt run --select silver.faker_returns` succeeds

- [ ] Task 5: Create `models/silver/faker/schema.yml` (AC: 5)
  - [ ] Declare all four models with `description`
  - [ ] Each model: at least one test (e.g. `unique` + `not_null` on the business primary key)
  - [ ] Every column documented with `description`, `data_type`, `meta: {pii: true/false}`
  - [ ] Columns `_loaded_at` and `_source` documented for each model
  - [ ] VERIFY: `dbt compile` succeeds; `yamllint models/silver/faker/schema.yml` passes

- [ ] Task 6: Remove `.gitkeep` from `models/silver/` (AC: 1)
  - [ ] Delete `models/silver/.gitkeep` — it was a placeholder; replace with real files

- [ ] Task 7: Full run and idempotency verification (AC: 1, 2, 3)
  - [ ] Ensure Bronze is populated: `python ingest/dlt_file_source.py`
  - [ ] Run: `dbt run --select tag:silver` — all four models succeed
  - [ ] Inspect schema: confirm `_loaded_at` and `_source` present on each Silver table
  - [ ] Run again: `dbt run --select tag:silver` — row counts unchanged (idempotency)
  - [ ] Run: `dbt test --select tag:silver` — all tests pass

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
