# Story 2.12b: Silver Incremental Idempotency Fix

Status: done

## Story

As a data engineer,
I want `make run-pipeline` to produce identical row counts and pass all dbt tests on every run against unchanged source data,
so that the pipeline is trustworthy and learner e2e testing is not broken by spurious uniqueness failures.

## Acceptance Criteria

1. **Given** Bronze is populated and Silver has been built at least once, **When** I run `make run-pipeline` a second time without regenerating source data, **Then** both runs exit 0, Silver and Gold row counts are identical, and `dbt test` passes on all models both times.

## Tasks / Subtasks

- [x] Task 0: Create story branch
  - [x] `git checkout -b story/2-12b-silver-incremental-idempotency-fix`
  - [x] Confirm working tree is clean before starting implementation

- [x] Task 1: Fix `faker_customers.sql` — change `unique_key` and dedup partition to business PK (AC: 1)
  - [x] Change `unique_key` in `{{ config(...) }}` from `'_dlt_id'` to `'customer_id'`
  - [x] Change dedup CTE `PARTITION BY _dlt_id` to `PARTITION BY customer_id`
  - [x] VERIFY: `dbt run --select faker_customers` succeeds (use `--full-refresh` once to reset, then run again normally)

- [x] Task 2: Fix `faker_products.sql` — same pattern (AC: 1)
  - [x] Change `unique_key` from `'_dlt_id'` to `'product_id'`
  - [x] Change dedup CTE `PARTITION BY _dlt_id` to `PARTITION BY product_id`
  - [x] VERIFY: `dbt run --select faker_products` succeeds

- [x] Task 3: Fix `faker_orders.sql` — same pattern (AC: 1)
  - [x] Change `unique_key` from `'_dlt_id'` to `'order_id'`
  - [x] Change dedup CTE `PARTITION BY _dlt_id` to `PARTITION BY order_id`
  - [x] VERIFY: `dbt run --select faker_orders` succeeds

- [x] Task 4: Fix `faker_returns.sql` — same pattern (AC: 1)
  - [x] Change `unique_key` from `'_dlt_id'` to `'return_id'`
  - [x] Change dedup CTE `PARTITION BY _dlt_id` to `PARTITION BY return_id`
  - [x] VERIFY: `dbt run --select faker_returns` succeeds

- [x] Task 5: Full reset and idempotency validation (AC: 1)
  - [x] Run `dbt run --select tag:silver --full-refresh` to reset Silver tables to a clean state
  - [x] Run `make run-pipeline` — record Silver and Gold row counts, confirm `dbt test` passes
  - [x] Run `make run-pipeline` a second time — confirm identical row counts and `dbt test` passes
  - [x] VERIFY: both runs exit 0; zero uniqueness failures

## Dev Notes

### Root Cause — Why `_dlt_id` Is Not a Stable Deduplication Key

dlt generates `_dlt_id` as a **per-row UUID assigned at load time**, not a content hash. When `dlt_file_source.py` runs a second time on the same CSV files, it assigns new UUIDs to every row:

```
Run 1:  customer_id="cust-1"  _dlt_id="uuid-A"  _dlt_load_id="1712345678"
Run 2:  customer_id="cust-1"  _dlt_id="uuid-B"  _dlt_load_id="1712349999"
```

Bronze now contains **two rows for the same customer**. The Silver incremental filter (`WHERE _dlt_load_id > MAX(...)`) correctly picks up Run 2's rows. The `delete+insert` strategy deletes rows matching `_dlt_id = "uuid-B"` (none yet in Silver), then inserts the new row. Run 1's row (`_dlt_id = "uuid-A"`) is **never deleted** because the unique_key doesn't match it.

Result: Silver contains both `uuid-A` and `uuid-B` rows for `customer_id="cust-1"` → **uniqueness test failure on `customer_id`**.

### The Fix — Use Business PK as `unique_key`

Changing `unique_key` to the business primary key (`customer_id`, `product_id`, `order_id`, `return_id`) makes `delete+insert` operate on the stable business identifier. On the second run:

1. Silver incremental filter picks up new Bronze rows (new `_dlt_load_id`)
2. Dedup CTE selects the latest row per business PK from the batch
3. `delete+insert` **deletes existing Silver rows** where `customer_id` matches, then inserts the new rows
4. Result: one Silver row per business PK, row counts unchanged ✅

### Exact Code Change Pattern (apply to all four models)

**Before (current — broken):**
```sql
{{ config(
    unique_key="_dlt_id",
    incremental_strategy="delete+insert"
) }}

...

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY _dlt_id ORDER BY _dlt_load_id DESC
        ) AS _row_num
    FROM source_data
),
```

**After (fixed):**
```sql
{{ config(
    unique_key="customer_id",          -- use the business PK for this model
    incremental_strategy="delete+insert"
) }}

...

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id   -- match the business PK
            ORDER BY _dlt_load_id DESC
        ) AS _row_num
    FROM source_data
),
```

### Business PK per Model

| Model | Old `unique_key` | New `unique_key` | Dedup partition |
|---|---|---|---|
| `faker_customers` | `_dlt_id` | `customer_id` | `PARTITION BY customer_id` |
| `faker_products` | `_dlt_id` | `product_id` | `PARTITION BY product_id` |
| `faker_orders` | `_dlt_id` | `order_id` | `PARTITION BY order_id` |
| `faker_returns` | `_dlt_id` | `return_id` | `PARTITION BY return_id` |

### `_dlt_id` Column Is Not Affected

The `_dlt_id` column remains in the SELECT output and in `schema.yml` — it is still a useful audit column showing which dlt batch row the record came from. Only its role as `unique_key` and dedup partition changes. The `unique` and `not_null` tests on `_dlt_id` in `schema.yml` should be **removed** — after the fix, multiple `_dlt_id` values for the same business PK can legitimately coexist in Bronze, so `_dlt_id` is no longer unique in Silver. Tests on business PK columns (`customer_id`, `product_id`, `order_id`, `return_id`) already cover uniqueness and are correct.

### Why `--full-refresh` Is Needed Once

The existing Silver tables contain duplicate rows from previous pipeline runs. `--full-refresh` drops and recreates the Silver tables, giving the fixed models a clean starting state. After that, normal incremental runs work correctly forever.

```bash
dbt run --select tag:silver --full-refresh   # one-time reset
dbt test --select tag:silver                 # confirm clean state
```

`--full-refresh` is only needed once to recover the corrupted Silver state. All subsequent `make run-pipeline` invocations use normal incremental mode.

### Incremental Filter (`_dlt_load_id` varchar) — Not Addressed Here

The existing `WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})` varchar comparison is a known deferred issue from story 2.4. It works correctly for current dlt decimal-string format and is **out of scope for this story**. Do not change the incremental filter — changing only `unique_key` and the dedup partition is sufficient to fix the idempotency failure.

### Scope Boundaries

| In scope | Out of scope |
|---|---|
| Change `unique_key` in all 4 Silver models | `_dlt_load_id` varchar comparison fix |
| Change dedup `PARTITION BY` to business PK | Gold or Quarantine model changes |
| Remove `unique`/`not_null` tests from `_dlt_id` in `schema.yml` | jsonplaceholder API source models |
| One-time `--full-refresh` to reset Silver state | Adding new tests beyond removing `_dlt_id` uniqueness |
| Confirm idempotency via two `make run-pipeline` runs | Changes to ingest scripts |

### ZScaler / dbt deps Warning

Do NOT run `dbt deps` during validation — use existing `dbt_packages/` on disk. See `docs/troubleshooting-dbt-deps-zscaler-tls.md`.

### Origin of This Bug

Traced from `deferred-work.md`:
- **"Deferred from: story 2-12 validation (2026-04-01)"**: second `make run-pipeline` run fails uniqueness tests on `faker_customers.customer_id`, `faker_products.product_id`, `faker_orders.order_id`, `faker_returns.return_id`, `dim_customers.customer_id`, `dim_products.product_id`, `fct_orders.order_id`, `orders_mart.order_id`.
- **"Deferred from: code review of 2-4 (2026-03-31)"**: `_dlt_load_id` varchar comparison and `delete+insert` deduplication deferred holistically.

The Gold-layer uniqueness failures (`fct_orders`, `dim_customers`, etc.) are downstream symptoms — fixing Silver deduplication will resolve them automatically since Gold reads from Silver via `{{ ref() }}`.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-04-01 14:23 BST - `dbt run --select faker_customers --full-refresh`
- 2026-04-01 14:25 BST - Sequentially verified `dbt run --select faker_customers`, `faker_products`, `faker_orders`, and `faker_returns`
- 2026-04-01 14:25 BST - `dbt run --select tag:silver --full-refresh`
- 2026-04-01 14:25 BST - First `make run-pipeline` completed successfully
- 2026-04-01 14:26 BST - Second `make run-pipeline` completed successfully with identical row counts

### Completion Notes List

- Switched all four Faker Silver incremental models from `_dlt_id` to the relevant business primary key for both `unique_key` and the batch deduplication window partition.
- Removed `unique` and `not_null` tests from the Silver `_dlt_id` columns and updated their descriptions to reflect lineage/audit usage instead of uniqueness semantics.
- Verified the one-time recovery path with `dbt run --select tag:silver --full-refresh`, then ran `make run-pipeline` twice successfully with stable row counts across Silver and Gold.
- Recorded matching post-run counts on both pipeline executions: `silver.faker_customers=1000`, `silver.faker_products=1000`, `silver.faker_orders=1000`, `silver.faker_returns=609`, `gold.dim_customers=1000`, `gold.dim_products=1000`, `gold.fct_orders=1000`, `gold.orders_mart=1000`.
- During per-model verification, parallel dbt runs hit DuckDB's single-writer file lock; rerunning the affected model checks sequentially resolved this without any code changes.

### File List

- models/silver/faker/faker_customers.sql (modified — unique_key and dedup partition)
- models/silver/faker/faker_products.sql (modified — unique_key and dedup partition)
- models/silver/faker/faker_orders.sql (modified — unique_key and dedup partition)
- models/silver/faker/faker_returns.sql (modified — unique_key and dedup partition)
- models/silver/faker/schema.yml (modified — remove unique/not_null tests from _dlt_id columns)
- _bmad-output/implementation-artifacts/2-12b-silver-incremental-idempotency-fix.md
- _bmad-output/implementation-artifacts/sprint-status.yaml

## Review Findings

- [x] [Review][Dismiss] Blind Hunter: "business key uniqueness now untested" — FALSE POSITIVE; `unique` and `not_null` tests on all four business PK columns (`customer_id`, `product_id`, `order_id`, `return_id`) were already present in `schema.yml` and are unchanged by this story
- [x] [Review][Dismiss] Blind Hunter: "`_dlt_id` deduplication semantics changed without documentation" — fully documented in Dev Notes section and `schema.yml` `_dlt_id` column descriptions
- [x] [Review][Defer] Blind Hunter / Edge Case Hunter: NULL business key could cause `delete+insert` to wipe rows — Faker generator produces UUIDs; `not_null` test guards against NULLs; pre-existing limitation of `delete+insert` strategy; address holistically if nullable business keys are introduced
- [x] [Review][Defer] Edge Case Hunter: non-deterministic `ROW_NUMBER` on tied `_dlt_load_id` values — pre-existing pattern; same batch never produces two rows with the same business PK in Faker source data; out of scope for this story
- [x] [Review][Defer] Edge Case Hunter: `_dlt_load_id` varchar watermark fragility — explicitly out of scope (noted in story Dev Notes); pre-existing from story 2.4 deferred work
- [x] [Review][Defer] Edge Case Hunter: soft-delete invisibility — pre-existing; Bronze is append-only; documented in story 2.4 deferred work
- [x] [Review][Pass] Acceptance Auditor: CLEAN — all AC satisfied, scope boundaries respected

## Change Log

- 2026-04-01: Story created — ready-for-dev
- 2026-04-01: Implemented Silver incremental idempotency fix, removed `_dlt_id` uniqueness tests, validated two successful `make run-pipeline` runs with identical Silver/Gold row counts, and moved story to review.
- 2026-04-01: Code review complete — 0 patches, 4 deferred, 2 dismissed. Story moved to done.
