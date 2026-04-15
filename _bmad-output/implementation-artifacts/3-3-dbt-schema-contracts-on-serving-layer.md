# Story 3.3: dbt Schema Contracts on Serving Layer

Status: review

## Story

As a data engineer,
I want dbt schema contracts enforced on all Gold/mart models,
So that downstream consumers (BI tools, the semantic layer) fail fast and explicitly if the serving layer schema changes unexpectedly.

## Acceptance Criteria

1. **Given** Gold models have `constraints` blocks in `schema.yml`, **When** I run `dbt run --select tag:gold`, **Then** dbt enforces the contract and the run succeeds with no contract violations on clean data.

2. **Given** I modify a Gold model to remove a contracted column, **When** I run `dbt run --select tag:gold`, **Then** the run fails with a clear contract violation error identifying the missing column.

## Tasks / Subtasks

- [x] Task 0: Create story branch (AC: all)
  - [x] `git checkout -b story/3-3-dbt-schema-contracts-on-serving-layer`
  - [x] Confirm working tree is clean

- [x] Task 1: Add `constraints:` blocks to Gold schema.yml files (AC: 1, 2)
  - [x] **`models/gold/facts/schema.yml`** — add `constraints:` to `fct_orders`:
    - `order_id`: add `constraints: [{type: not_null}, {type: primary_key}]`
    - `customer_id`: add `constraints: [{type: not_null}]`
    - `product_id`: add `constraints: [{type: not_null}]`
    - `order_date`: add `constraints: [{type: not_null}]`
  - [x] **`models/gold/dimensions/schema.yml`** — add `constraints:` to `dim_customers` and `dim_products`:
    - `dim_customers.customer_id`: add `constraints: [{type: not_null}, {type: primary_key}]`
    - `dim_products.product_id`: add `constraints: [{type: not_null}, {type: primary_key}]`
  - [x] **`models/gold/marts/schema.yml`** — add `constraints:` to `orders_mart`:
    - `orders_mart.order_id`: add `constraints: [{type: not_null}, {type: primary_key}]`
  - [x] VERIFY: `config: contract: enforced: true` is still present and unchanged on all four models (do NOT remove it — it was set in earlier stories)
  - [x] VERIFY: All column `data_type` declarations remain intact (contract enforcement requires both `data_type` and `constraints:`)
  - [x] VERIFY: `dbt compile --select tag:gold` exits 0 (validates contract syntax without DB)

- [x] Task 2: Add `dbt-verify-contracts` Makefile target (AC: 1)
  - [x] Add `dbt-verify-contracts` to the `.PHONY` line at top of `Makefile`
  - [x] Add target after `pg-show-pii-log`:
    ```makefile
    dbt-verify-contracts: ## Compile Gold models to verify schema contract syntax (no DB required)
    	dbt compile --select tag:gold
    ```
  - [x] VERIFY: `make dbt-verify-contracts` exits 0

- [x] Task 3: Write tests `tests/test_story_3_3_schema_contracts.py` (AC: 1, 2)
  - [x] Test that `contract: enforced: true` is declared in all four Gold schema.yml files:
    - `models/gold/facts/schema.yml`
    - `models/gold/dimensions/schema.yml`
    - `models/gold/marts/schema.yml`
  - [x] Test that every Gold model column has a `data_type` declaration (no column missing `data_type:`)
  - [x] Test that primary key columns in all four Gold models have `constraints:` blocks:
    - `fct_orders.order_id` has `not_null` and `primary_key` constraint types
    - `dim_customers.customer_id` has `not_null` and `primary_key` constraint types
    - `dim_products.product_id` has `not_null` and `primary_key` constraint types
    - `orders_mart.order_id` has `not_null` and `primary_key` constraint types
  - [x] Test that the `dbt-verify-contracts` target is declared in `Makefile`

- [x] Task 4: Manual verification — demonstrate fail-fast behavior (AC: 2)
  - [x] With `COMPOSE_PROFILES=postgres` active, run `dbt run --select tag:gold` — confirm clean run
  - [x] Temporarily rename `order_id` to `order_id_renamed` in `fct_orders.sql` final SELECT
  - [x] Run `dbt run --select fct_orders` — confirm error message references the missing contracted column
  - [x] Revert `fct_orders.sql` to original
  - [x] Confirm clean `dbt run --select tag:gold` after revert

- [x] Task 5: Update sprint status
  - [x] `_bmad-output/implementation-artifacts/sprint-status.yaml`: update `3-3-dbt-schema-contracts-on-serving-layer` → `done` (after verification passes)

## Dev Notes

### What Is Already in Place (Do NOT Remove)

All four Gold schema.yml files already have `config: contract: enforced: true` set — this was introduced in earlier stories (Story 2.6 / Story 3.2 context). **Do NOT remove or modify these blocks.**

The `config: contract: enforced: true` setting causes dbt to:
1. Materialise the table with an explicit column definition list (not `CREATE TABLE AS SELECT`)
2. Reject the build if any declared column name or `data_type` does not match the model SQL output

This story adds the missing `constraints:` blocks (DB-level DDL constraints) alongside the already-present contract enforcement.

### What Needs to Be Added

The architecture rule ([Source: `_bmad-output/planning-artifacts/architecture.md`, schema.yml Completeness Rule]):
> Gold/mart models must additionally have: `constraints` block (dbt contract enforcement)

The current schema.yml files satisfy the `config: contract: enforced: true` requirement but are missing the column-level `constraints:` blocks. This story adds them.

### Correct YAML Syntax for dbt 1.11.7 Column Constraints

```yaml
- name: order_id
  description: "UUID primary key for the order."
  data_type: varchar
  meta: {pii: false}
  constraints:
    - type: not_null
    - type: primary_key
  tests:
    - unique
    - not_null
```

**Key rules:**
- `constraints:` is a sibling of `tests:`, `data_type:`, `description:`, `meta:` — not nested inside them
- `type: primary_key` implies `NOT NULL` in Postgres, but adding `type: not_null` separately is correct and self-documenting
- Keep existing `tests:` entries unchanged — `constraints:` (DB-level DDL) and `tests:` (dbt data quality checks) serve different purposes
- Do NOT add `constraints:` to every column — add only to columns where a DB-level constraint makes semantic sense (primary keys and explicit not_null business keys)

### Cross-Profile Compatibility

`schema.yml` is shared across all profiles (simple = DuckDB, postgres = Postgres). Changes here affect both.

- **dbt-duckdb ≥1.8.x** (current): supports `not_null` and `primary_key` constraints at column level; DuckDB 1.1.x enforces them at table creation
- **dbt-postgres 1.10.0**: full constraint support — Postgres creates actual `NOT NULL` and `PRIMARY KEY` DDL constraints
- **Result**: adding `constraints:` to Gold schema.yml is safe for both profiles

### Three-Tier Portability — Tier 1 Only

Schema contracts (`config: contract: enforced: true` + `constraints:`) are dbt-declared (Tier 1/Tier 2). This is NOT engine-native Tier 3 (unlike the RBAC/masking from Story 3.2). The `constraints:` blocks are portable and correct to place in shared `schema.yml`.

Do NOT add contract enforcement SQL to `docker/init/` files — that would be a Tier 3 mistake.

### Contract Fail-Fast Mechanism

When `contract: enforced: true` and a column is removed or renamed in the model SQL output:

```
Compilation Error in model fct_orders (models/gold/facts/fct_orders.sql)
  Contract for model 'fct_orders':
    Expected column 'order_id' of type 'varchar' in model output, but it was not found
```

dbt fails at compile/build time before any DML executes. This is the fail-fast behavior satisfying AC2.

### Models With `SELECT *` — No Issue

`fct_orders.sql` uses `SELECT * FROM final` where `final` is a CTE with fully-explicit column aliases. The contract checks the resolved output columns, not the literal SQL text — so `SELECT *` from a fully-aliased CTE passes contract validation correctly.

### Files to Touch

| File | Change |
|------|--------|
| `models/gold/facts/schema.yml` | Add `constraints:` to `order_id`, `customer_id`, `product_id`, `order_date` |
| `models/gold/dimensions/schema.yml` | Add `constraints:` to `dim_customers.customer_id`, `dim_products.product_id` |
| `models/gold/marts/schema.yml` | Add `constraints:` to `orders_mart.order_id` |
| `Makefile` | Add `dbt-verify-contracts` target |
| `tests/test_story_3_3_schema_contracts.py` | New — structural verification tests |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Update story status |

**Do NOT touch:**
- `docker/init/postgres_init.sql` — Story 3.1 RBAC baseline; do not modify
- `docker/init/postgres_masking.sql` — Story 3.2 masking; do not modify
- Any Silver, Bronze, or Quarantine `schema.yml` — contracts are Gold-only per architecture
- Any `.sql` model files — constraints are declared in `schema.yml`, not in SQL
- `requirements.txt` — no new Python dependencies
- `docker-compose.yml` — no changes needed

### Previous Story Intelligence (Story 3.2)

- Tests use structural assertions (`assertIn`, `Path.read_text()`) — no DB connectivity required
- Test class naming convention: `Story3{N}DescriptiveNameTests` → use `Story33SchemaContractsTests`
- `PROJECT_ROOT = Path(__file__).resolve().parents[1]` at top of test file
- Story 3.2 patch history: verify `.PHONY` is updated alongside any new Makefile target
- Story 3.2 dev note confirmed: "Story 3.3 adds `constraints:` blocks to Gold model `schema.yml` files for dbt schema contracts."

### Parsing Gold schema.yml in Tests

The tests can use `yaml.safe_load()` (PyYAML is already available in the project via dbt) to parse schema.yml files, or use `read_text()` with `assertIn` for simpler structural checks. Using `yaml.safe_load` is more robust for verifying nested constraint structures.

Example test pattern:
```python
import yaml
schema = yaml.safe_load((PROJECT_ROOT / "models/gold/facts/schema.yml").read_text())
fct_orders = next(m for m in schema["models"] if m["name"] == "fct_orders")
self.assertTrue(fct_orders["config"]["contract"]["enforced"])
order_id_col = next(c for c in fct_orders["columns"] if c["name"] == "order_id")
constraint_types = [c["type"] for c in order_id_col["constraints"]]
self.assertIn("not_null", constraint_types)
self.assertIn("primary_key", constraint_types)
```

### Verification Commands

```bash
# Compile only — no DB required
dbt compile --select tag:gold

# Full run on postgres profile
set -a; . ./.env; set +a; COMPOSE_PROFILES=postgres dbt run --select tag:gold

# Fail-fast demonstration (revert after)
# 1. Edit fct_orders.sql: rename order_id → order_id_renamed in final CTE
# 2. Run: dbt run --select fct_orders  → expect contract violation error
# 3. Revert the edit
# 4. Run: dbt run --select fct_orders  → confirm clean run
```

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `python tests/test_story_3_3_schema_contracts.py`
- `make dbt-verify-contracts`
- `python -m unittest discover tests`
- `set -a; . ./.env; set +a; COMPOSE_PROFILES=postgres dbt run --select tag:gold`
- Temporary verification only: renamed `order_id` to `order_id_renamed` in `models/gold/facts/fct_orders.sql`, then ran `set -a; . ./.env; set +a; COMPOSE_PROFILES=postgres dbt run --select fct_orders`

### Completion Notes List

- Added dbt column `constraints:` metadata for all contracted Gold primary keys and required business keys while preserving existing `contract.enforced` and `data_type` declarations.
- Added `dbt-verify-contracts` to the Makefile so contract syntax can be verified without a live database.
- Added structural regression tests covering contract enforcement flags, required `data_type` declarations, primary key constraints, and the new Make target.
- Verified fail-fast contract behavior on the postgres profile: renaming `order_id` produced a contract error showing `order_id` as missing from the definition and `order_id_renamed` as missing from the contract, then the clean run passed again after revert.
- Branch was created from a worktree that already contained unrelated untracked items (`.claude/worktrees/`, `.codex-worktrees/`, and this story file), so the tree was not globally clean even though story implementation changes were isolated to this branch and committed separately.

### File List

- Makefile
- models/gold/facts/schema.yml
- models/gold/dimensions/schema.yml
- models/gold/marts/schema.yml
- tests/test_story_3_3_schema_contracts.py
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/3-3-dbt-schema-contracts-on-serving-layer.md

### Change Log

- 2026-04-15: Added Gold schema constraints, a Makefile contract verification target, structural tests, postgres fail-fast verification evidence, and moved the story to review.
