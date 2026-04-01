# Story 2.8: dbt Tests, dbt-expectations, and Source Freshness

Status: done

## Story

As a data engineer,
I want comprehensive dbt tests (generic, dbt-expectations, and source freshness checks) running after every pipeline execution,
So that data quality issues surface as visible failures rather than silent data corruption.

## Acceptance Criteria

1. **Given** dbt tests are declared in `schema.yml` for all Silver and Gold models **When** I run `dbt test` **Then** all tests pass on a clean run with default sample data.

2. **Given** I intentionally introduce a type mismatch in a Silver model **When** I run `dbt test` **Then** the relevant test fails and the error message identifies the model and column.

3. **Given** source freshness thresholds are declared in `models/bronze/sources.yml` **When** I run `dbt source freshness` **Then** freshness status (pass/warn/error) is reported per source.

4. **Given** dbt-expectations is installed via `packages.yml` **When** I run `dbt deps && dbt test` **Then** dbt-expectations tests run alongside generic tests without errors.

## Tasks / Subtasks

- [x] Task 1: Add source freshness thresholds to `models/bronze/sources.yml` (AC: 3)
  - [x] Add `loaded_at_field: created_at` and `freshness` block to the `faker_file` source definition
  - [x] Set `warn_after: {count: 30, period: day}` and `error_after: {count: 90, period: day}` at the source level
  - [x] No freshness on `jsonplaceholder` source (static dataset, noted as "not referenced by Silver models")
  - [x] VERIFY: `dbt source freshness --select source:faker_file` runs without error and reports status

- [x] Task 2: Add `accepted_values` and `not_null` tests to Silver `faker_orders` schema.yml (AC: 1, 2)
  - [x] `customer_id`: add `not_null` test
  - [x] `product_id`: add `not_null` test
  - [x] `status`: add `accepted_values: ['pending', 'shipped', 'delivered', 'cancelled', 'returned']`
  - [x] `unit_price`: add `dbt_expectations.expect_column_values_to_be_between` (min_value: 0, strictly: false)
  - [x] `total_amount`: add `dbt_expectations.expect_column_values_to_be_between` (min_value: 0, strictly: false)
  - [x] `quantity`: add `dbt_expectations.expect_column_values_to_be_between` (min_value: 1, strictly: false)
  - [x] `_source`: add `accepted_values: ['faker_orders_file']`
  - [x] VERIFY: `dbt test --select faker_orders` passes

- [x] Task 3: Add `accepted_values` and `not_null` tests to Silver `faker_returns` schema.yml (AC: 1, 2)
  - [x] `order_id`: add `not_null` test
  - [x] `product_id`: add `not_null` test
  - [x] `reason`: add `accepted_values: ['defective', 'wrong_item', 'not_as_described', 'changed_mind', 'damaged_in_transit']`
  - [x] `refund_amount`: add `dbt_expectations.expect_column_values_to_be_between` (min_value: 0, strictly: false)
  - [x] `_source`: add `accepted_values: ['faker_returns_file']`
  - [x] VERIFY: `dbt test --select faker_returns` passes

- [x] Task 4: Add `accepted_values` tests to Silver `faker_customers` and `faker_products` schema.yml (AC: 1, 2)
  - [x] `faker_customers._source`: add `accepted_values: ['faker_customers_file']`
  - [x] `faker_products.category`: add `accepted_values: ['Electronics', 'Clothing', 'Home', 'Books', 'Sports', 'Toys']`
  - [x] `faker_products.unit_price`: add `dbt_expectations.expect_column_values_to_be_between` (min_value: 0, strictly: true)
  - [x] `faker_products._source`: add `accepted_values: ['faker_products_file']`
  - [x] VERIFY: `dbt test --select faker_customers faker_products` passes

- [x] Task 5: Add `accepted_values` tests to Gold schema.yml files (AC: 1)
  - [x] `models/gold/facts/schema.yml` → `fct_orders._source`: add `accepted_values: ['fct_orders']`
  - [x] `models/gold/dimensions/schema.yml` → `dim_customers._source`: add `accepted_values: ['dim_customers']`
  - [x] `models/gold/dimensions/schema.yml` → `dim_products._source`: add `accepted_values: ['dim_products']`
  - [x] `models/gold/marts/schema.yml` → `orders_mart._source`: add `accepted_values: ['orders_mart']`
  - [x] VERIFY: `dbt test --select tag:gold` passes

- [x] Task 6: Full validation (AC: 1, 4)
  - [x] Run `dbt deps` — confirm no package errors (packages already installed in `dbt_packages/`, this is a no-op)
  - [x] Run `dbt test` — all tests pass across Silver, Gold, Quarantine layers
  - [x] Run `dbt source freshness` — `faker_file` tables report freshness status
  - [x] Run `dbt build` — no regressions
  - [x] Run `PYTHONPATH=. pytest -q tests` — Python tests pass

## Dev Notes

### What Is Already in Place — Do Not Re-install or Re-declare

**`packages.yml` is already complete — do NOT modify it:**
```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0"]
  - package: elementary-data/elementary
    version: [">=0.20.0"]
  - package: calogica/dbt_expectations
    version: [">=0.10.0"]
```

**`dbt_packages/` directory already exists** — `dbt deps` was already run (you can see `dbt_packages/dbt_expectations/` and `dbt_packages/elementary/` on disk). Running `dbt deps` again is a safe no-op.

**Do not touch:**
- `models/bronze/sources.yml` column definitions — only add the `freshness` block to the source and `loaded_at_field` to source tables
- Any Silver or Gold SQL model files — this story adds tests to `schema.yml` files only
- `packages.yml` — already complete
- `macros/generate_schema_name.sql` — already in place; Gold materialization routes automatically

### Source Freshness Pattern

Add `loaded_at_field` and `freshness` to each `faker_file` table that has a `created_at` column. **Use `created_at` as the freshness field** — this is a practical choice for the simple profile where `_dlt_load_id` is a varchar Unix timestamp string (not directly usable as a dbt freshness field without casting).

**Add at the `faker_file` source level** (applies to all tables unless overridden):
```yaml
sources:
  - name: faker_file
    description: "..."
    schema: bronze
    loaded_at_field: created_at        # ← add this at source level
    freshness:                          # ← add this at source level
      warn_after: {count: 30, period: day}
      error_after: {count: 90, period: day}
    tables:
      - name: customers
        ...
      - name: orders
        ...
```

The `jsonplaceholder` source does **not** get freshness thresholds — it's a static dataset, not a live pipeline source.

### dbt-expectations Test Syntax (calogica/dbt_expectations >= 0.10.0)

Declare in the column's `tests:` list inside `schema.yml`:

```yaml
# Numeric range check
- dbt_expectations.expect_column_values_to_be_between:
    min_value: 0
    strictly: false    # false = >= 0, true = > 0

# For strictly positive values (e.g., unit_price must be > 0):
- dbt_expectations.expect_column_values_to_be_between:
    min_value: 0
    strictly: true
```

**Do NOT use** `dbt_expectations.expect_column_values_to_not_be_null` — use the built-in `not_null` test instead (identical behaviour, lower token cost).

### Standard dbt accepted_values Syntax

```yaml
- name: status
  tests:
    - accepted_values:
        values: ['pending', 'shipped', 'delivered', 'cancelled', 'returned']
```

### Standard dbt relationships Syntax (not in scope for 2.8)

FK relationship tests (`relationships`) were considered but are **deferred** — they require cross-schema queries in DuckDB during incremental runs and may produce unexpected results with the quarantine pattern. The `not_null` tests on FK columns achieve the primary safety goal.

### Silver _source Literal Values — Use Exactly These

| Silver model | Correct `_source` value |
|---|---|
| `faker_customers` | `'faker_customers_file'` |
| `faker_products` | `'faker_products_file'` |
| `faker_orders` | `'faker_orders_file'` |
| `faker_returns` | `'faker_returns_file'` |

These are hardcoded in the Silver SQL models. The `accepted_values` test must match exactly (case-sensitive).

### Gold _source Literal Values — Use Exactly These

| Gold model | Correct `_source` value |
|---|---|
| `fct_orders` | `'fct_orders'` |
| `dim_customers` | `'dim_customers'` |
| `dim_products` | `'dim_products'` |
| `orders_mart` | `'orders_mart'` |

### Gold Contract Schema Warning

Gold schema.yml files use `config: contract: enforced: true`. Adding `tests:` to an existing column entry does **not** break contract enforcement — tests are supplemental metadata. Do not modify `data_type`, column order, or the `config` block.

**Column order in Gold schema.yml must match SELECT column order** — do not reorder columns when adding tests. Just add `tests:` to the existing column entry.

### Scope Boundaries

| In scope | Out of scope |
|---|---|
| Add source freshness to `sources.yml` | Elementary dashboard setup (Story 2.9) |
| Add dbt-expectations numeric tests to Silver | Fix `_dlt_load_id` varchar comparison in Silver SQL |
| Add accepted_values to Silver + Gold `_source` cols | Adding relationship FK tests |
| Add not_null to FK columns in Silver | Modifying Silver or Gold SQL model files |
| Add category/status/reason accepted_values | Adding singular tests in `tests/` directory |
| Verify `dbt build` passes end-to-end | MetricFlow semantic layer (Story 2.7) |

### Deferred Work Explicitly Assigned to This Story

From `_bmad-output/implementation-artifacts/deferred-work.md`:

- **2.6 review**: `_source` literal hardcoded with no `accepted_values` test across all Gold models → **Tasks 5**
- **2.5 review**: No extended model-level tests (accepted_values, row-count) → **Tasks 2–5**
- **2.4 review**: Missing `total_amount` integrity, FK `not_null` guards on `faker_orders`/`faker_returns`, `unit_price` non-negative constraint → **Tasks 2–3**

The `_dlt_load_id` varchar comparison issue (also deferred from 2.4) is **NOT addressed here** — that requires modifying Silver SQL models and is a holistic Silver refactor, not a test addition.

### Regression Check

After all schema.yml additions, run:

```bash
dbt test --select tag:silver     # Silver tests pass (including new ones)
dbt test --select tag:gold       # Gold tests pass (including new _source accepted_values)
dbt source freshness             # faker_file tables report freshness status
dbt build                        # full build — no regressions anywhere
PYTHONPATH=. pytest -q tests     # Python tests still pass
```

## Dev Agent Record

### Implementation Plan

- Add source freshness metadata to the `faker_file` source only, keeping Bronze column declarations unchanged.
- Extend Silver Faker schema tests in task order with built-in `not_null` and `accepted_values`, plus `dbt_expectations` numeric range checks.
- Extend Gold schema files with `_source` accepted-values tests without changing column order or contract metadata.
- Validate with targeted dbt commands first, then full `dbt deps`, `dbt test`, `dbt source freshness`, `dbt build`, and `PYTHONPATH=. pytest -q tests`.

### Debug Log

- Added source freshness metadata to `models/bronze/sources.yml` for the `faker_file` source only.
- Added the required Silver and Gold `accepted_values`, `not_null`, and `dbt_expectations` tests in schema metadata without modifying SQL models or Gold contract structure.
- The shared `dev.duckdb` file was locked by another local Python process, so targeted dbt validation ran successfully against an isolated temporary copy at `/tmp/story-2-8-dbt/dev.duckdb`.
- Verified targeted commands successfully before the dependency restore attempt: `dbt source freshness --select source:faker_file`, `dbt test --select faker_orders`, `dbt test --select faker_returns`, `dbt test --select faker_customers faker_products`, and `dbt test --select tag:gold`.
- `dbt deps` failed first on sandbox DNS resolution and then outside the sandbox with local TLS certificate verification errors against `hub.getdbt.com`; during that failure, dbt cleaned `dbt_packages/`, which blocked the remaining full-project dbt commands from compiling.
- `PYTHONPATH=. pytest -q tests` still passed (`5 passed`).
- After sourcing the updated `~/.zshrc`, Python picked up `/Users/iain.livingstone/.certs/cacert.pem` for `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE`, which resolved the Zscaler-intercepted TLS validation issue.
- Restored packages successfully with `dbt deps`, then completed the full validation suite against `/tmp/story-2-8-dbt/dev.duckdb`: `dbt test`, `dbt source freshness`, `dbt build`, and `PYTHONPATH=. pytest -q tests`.

### Completion Notes

- Implemented all requested source freshness and schema test metadata for Bronze, Silver, and Gold models.
- Targeted verification passed for Tasks 1-5 on an isolated DuckDB copy because the shared local database file was locked by another process.
- Captured the TLS diagnosis and recovery notes in `docs/troubleshooting-dbt-deps-zscaler-tls.md` for future reference.
- Full validation now passes after sourcing the new CA bundle from `~/.zshrc` and restoring `dbt_packages/` with `dbt deps`.

## File List

- models/bronze/sources.yml (modified — freshness block added)
- models/silver/faker/schema.yml (modified — new tests on multiple columns)
- models/gold/facts/schema.yml (modified — accepted_values on _source)
- models/gold/dimensions/schema.yml (modified — accepted_values on _source)
- models/gold/marts/schema.yml (modified — accepted_values on _source)
- _bmad-output/implementation-artifacts/2-8-dbt-tests-dbt-expectations-and-source-freshness.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- docs/troubleshooting-dbt-deps-zscaler-tls.md

## Review Findings

- [x] [Review][Decision] `faker_orders.unit_price` allows $0 but `faker_products.unit_price` forbids it — resolved: `strictly: false` is intentional; $0 orders represent promotional/free items. Documented in column description and inline comment in schema.yml. [models/silver/faker/schema.yml]
- [x] [Review][Decision] `faker_returns.refund_amount` test allows $0 (`strictly: false`) but `models/bronze/sources.yml` documents refund_amount as "50-100% of original total_amount" — resolved: `strictly: false` is intentional as a defensive floor guard; percentage-range enforcement is out of scope. Documented in column description and inline comment in schema.yml. [models/silver/faker/schema.yml]
- [x] [Review][Defer] `order_date` and `return_date` have no `not_null` or temporal range tests — FK columns were guarded but temporal keys remain uncovered; deferred, pre-existing gap
- [x] [Review][Defer] No upper-bound tests on `quantity`, `unit_price`, or `total_amount` — extreme outliers from Faker or data corruption would pass silently; deferred, pre-existing gap

## Change Log

- 2026-04-01: Story created — ready for dev
- 2026-04-01: Implemented source freshness and Silver/Gold schema tests; targeted dbt verification passed, but full validation remains blocked by `dbt deps` TLS failures restoring `dbt_packages/`.
- 2026-04-01: Restored `dbt deps` with the updated CA bundle, completed full dbt and pytest validation, and moved the story to review.
