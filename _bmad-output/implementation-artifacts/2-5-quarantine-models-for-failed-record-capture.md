# Story 2.5: Quarantine Models for Failed Record Capture

Status: ready-for-dev

## Story

As a data engineer,
I want failed records from Silver models to land in a dedicated quarantine schema with failure context,
So that pipeline failures are visible and diagnosable without hunting through logs.

## Acceptance Criteria

1. **Given** a Silver model encounters records that fail validation rules, **When** the dbt pipeline runs, **Then** rejected records land in `quarantine.faker_customers_failed`, `quarantine.faker_products_failed`, `quarantine.faker_orders_failed`, `quarantine.faker_returns_failed`; each record includes the original row data plus `_failed_reason` (varchar) and `_failed_at` (timestamp).

2. **Given** the DuckDB init runs on `make start`, **When** I inspect the DuckDB schemas, **Then** the `quarantine` schema exists before any dbt run.

3. **Given** I run `make run-pipeline` twice on clean Faker data, **When** I query `quarantine.*`, **Then** quarantine tables exist but contain zero rows (clean Faker data passes all validation rules — idempotent clean run).

## Tasks / Subtasks

- [ ] Task 1: Create `models/quarantine/faker/faker_customers_failed.sql` (AC: 1, 3)
  - [ ] Config: `unique_key='_dlt_id'`, `incremental_strategy='delete+insert'` (materialization inherited from `dbt_project.yml`)
  - [ ] Source: `{{ source('faker_file', 'customers') }}`
  - [ ] Incremental filter: `{% if is_incremental() %} WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }}) {% endif %}`
  - [ ] Failed condition: `WHERE _dlt_id IS NULL OR customer_id IS NULL OR email IS NULL`
  - [ ] `_failed_reason`: CASE expression identifying the first failing rule (see SQL pattern below)
  - [ ] `_failed_at`: `CURRENT_TIMESTAMP`
  - [ ] All original Bronze columns included
  - [ ] VERIFY: `dbt run --select quarantine.faker_customers_failed` succeeds, zero rows on clean data

- [ ] Task 2: Create `models/quarantine/faker/faker_products_failed.sql` (AC: 1, 3)
  - [ ] Same incremental config and source pattern as faker_customers_failed
  - [ ] Source: `{{ source('faker_file', 'products') }}`
  - [ ] Failed condition: `WHERE _dlt_id IS NULL OR product_id IS NULL OR product_name IS NULL OR unit_price IS NULL OR unit_price <= 0`
  - [ ] `_failed_reason`: CASE expression per rule
  - [ ] VERIFY: `dbt run --select quarantine.faker_products_failed` succeeds, zero rows on clean data

- [ ] Task 3: Create `models/quarantine/faker/faker_orders_failed.sql` (AC: 1, 3)
  - [ ] Same incremental config and source pattern
  - [ ] Source: `{{ source('faker_file', 'orders') }}`
  - [ ] Failed condition: `WHERE _dlt_id IS NULL OR order_id IS NULL OR customer_id IS NULL OR product_id IS NULL OR quantity IS NULL OR quantity <= 0 OR total_amount IS NULL OR total_amount <= 0`
  - [ ] `_failed_reason`: CASE expression per rule
  - [ ] VERIFY: `dbt run --select quarantine.faker_orders_failed` succeeds, zero rows on clean data

- [ ] Task 4: Create `models/quarantine/faker/faker_returns_failed.sql` (AC: 1, 3)
  - [ ] Same incremental config and source pattern
  - [ ] Source: `{{ source('faker_file', 'returns') }}`
  - [ ] Failed condition: `WHERE _dlt_id IS NULL OR return_id IS NULL OR order_id IS NULL OR product_id IS NULL OR refund_amount IS NULL OR refund_amount <= 0`
  - [ ] `_failed_reason`: CASE expression per rule
  - [ ] VERIFY: `dbt run --select quarantine.faker_returns_failed` succeeds, zero rows on clean data

- [ ] Task 5: Create `models/quarantine/faker/schema.yml` (AC: 1)
  - [ ] Declare all four quarantine models with `description`
  - [ ] Each model: at least one test — `not_null` on `_dlt_id` and `_failed_reason`
  - [ ] Every column documented with `description`, `data_type`, `meta.pii: true/false`
  - [ ] `_failed_reason` and `_failed_at` must be documented on every model
  - [ ] VERIFY: `dbt compile --select tag:quarantine` succeeds

- [ ] Task 6: Initialise `quarantine` schema before dbt runs (AC: 2)
  - [ ] Check whether a DuckDB initialisation mechanism exists (Makefile, pre-hook, or script)
  - [ ] Add `CREATE SCHEMA IF NOT EXISTS quarantine` to the DuckDB init path so the schema exists after `make start` and before any `dbt run`
  - [ ] Simplest approach: add a `dbt run-operation` pre-step or a one-liner Python call in the Makefile's `run-pipeline` target (e.g. `python -c "import duckdb; c=duckdb.connect('dev.duckdb'); c.execute('CREATE SCHEMA IF NOT EXISTS quarantine'); c.close()"`)
  - [ ] VERIFY: `duckdb dev.duckdb -c ".schema"` shows `quarantine` schema even before `dbt run`

- [ ] Task 7: Remove `.gitkeep` from `models/quarantine/` (AC: 1)
  - [ ] Delete `models/quarantine/.gitkeep`

- [ ] Task 8: Full run verification (AC: 1, 2, 3)
  - [ ] Run `dbt run --select tag:quarantine` — all four models succeed
  - [ ] Verify each table has `_failed_reason` and `_failed_at` columns in schema
  - [ ] Verify zero rows in all quarantine tables on clean Faker data
  - [ ] Run a second time — row counts still zero (idempotency check)
  - [ ] Run `dbt test --select tag:quarantine` — all tests pass

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
