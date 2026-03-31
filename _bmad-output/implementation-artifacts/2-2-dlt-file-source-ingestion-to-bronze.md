# Story 2.2: dlt File Source Ingestion to Bronze

Status: done

## Story

As a data engineer,
I want dlt to ingest data from local file drops into the Bronze layer with full metadata stamping,
So that raw data lands immutably with auditable provenance before any transformation occurs.

## Acceptance Criteria

1. **Given** sample files exist in `data/`, **When** I run `python ingest/dlt_file_source.py`, **Then** raw records land in the `bronze` schema in `dev.duckdb` with zero modification to source values — all original columns present with original types.

2. **Given** Bronze tables are populated, **When** I inspect the table schema, **Then** `_dlt_load_id` and `_dlt_id` columns are present on every Bronze table (dlt native columns, not renamed) **And** no other metadata columns are added at the Bronze layer (no `_loaded_at`, no `_source` — these belong in Silver).

3. **Given** I run the file source pipeline twice on the same source files, **When** I count Bronze rows after each run, **Then** row count does not increase — dlt deduplicates using the entity primary key as `write_disposition="merge"`.

4. **Given** a pipeline run completes, **When** I inspect the `bronze` schema in DuckDB, **Then** no dbt materializations exist — the schema contains only dlt-written tables (`customers`, `products`, `orders`, `returns`, and dlt's own internal tracking tables).

## Tasks / Subtasks

- [ ] Task 1: Create `ingest/dlt_file_source.py` (AC: 1, 2, 3)
  - [ ] Read `FAKER_OUTPUT_DIR` env var (default: `data`) — same var as generator
  - [ ] Read `DBT_DUCKDB_PATH` env var (default: `dev.duckdb`) — same file dbt uses
  - [ ] Create dlt pipeline: `pipeline_name="faker_file"`, DuckDB destination at `DBT_DUCKDB_PATH`, `dataset_name="bronze"`
  - [ ] Create 4 dlt resources with `write_disposition="merge"`:
    - `customers` — `primary_key="customer_id"`
    - `products` — `primary_key="product_id"`
    - `orders` — `primary_key="order_id"`
    - `returns` — `primary_key="return_id"`
  - [ ] Each resource yields records from the corresponding JSON file in `FAKER_OUTPUT_DIR`
  - [ ] Wrap pipeline run in try/except — on failure print structured JSON and exit 1
  - [ ] Print load info summary on success: table name + row count for each entity
  - [ ] VERIFY: `python ingest/faker_generator.py && python ingest/dlt_file_source.py` — no errors, 4 tables created in bronze schema
  - [ ] VERIFY: `_dlt_load_id` and `_dlt_id` columns exist in all 4 bronze tables
  - [ ] VERIFY: No extra metadata columns (`_loaded_at`, `_source`, etc.) in Bronze tables

- [ ] Task 2: Verify idempotency AC3
  - [ ] Run pipeline twice on the same data files
  - [ ] VERIFY: Row count in bronze tables identical after both runs (no duplication)

- [ ] Task 3: Verify bronze ownership AC4
  - [ ] VERIFY: `dbt compile` succeeds (no bronze SQL models — already true from Story 1.1)
  - [ ] VERIFY: Only dlt-written tables exist in `bronze` schema — no dbt-created tables

- [ ] Task 4: Final AC check
  - [ ] AC1: All source columns present in bronze with correct values
  - [ ] AC2: `_dlt_load_id` and `_dlt_id` present; no Silver-level metadata columns
  - [ ] AC3: Second pipeline run does not increase row count
  - [ ] AC4: No dbt materializations in bronze schema

## Dev Notes

### dlt Pipeline Implementation Pattern

```python
#!/usr/bin/env python3
"""
dlt file source pipeline for local-data-platform.
Reads Faker-generated JSON files from data/ and loads to bronze schema in DuckDB.

Usage:
    python ingest/dlt_file_source.py
    DBT_DUCKDB_PATH=dev.duckdb FAKER_OUTPUT_DIR=data python ingest/dlt_file_source.py
"""
import json
import os
import sys
from pathlib import Path

import dlt

DATA_DIR = Path(os.environ.get("FAKER_OUTPUT_DIR", "data"))
DUCKDB_PATH = os.environ.get("DBT_DUCKDB_PATH", "dev.duckdb")

ENTITIES = {
    "customers": "customer_id",
    "products": "product_id",
    "orders": "order_id",
    "returns": "return_id",
}


def make_resource(entity: str, primary_key: str):
    @dlt.resource(name=entity, primary_key=primary_key, write_disposition="merge")
    def _resource():
        path = DATA_DIR / f"{entity}.json"
        with open(path) as f:
            yield json.load(f)
    _resource.__name__ = entity
    return _resource


@dlt.source
def faker_file_source():
    for entity, pk in ENTITIES.items():
        yield make_resource(entity, pk)


def main():
    try:
        pipeline = dlt.pipeline(
            pipeline_name="faker_file",
            destination=dlt.destinations.duckdb(DUCKDB_PATH),
            dataset_name="bronze",
        )
        load_info = pipeline.run(faker_file_source())
        print(load_info)
        for package in load_info.load_packages:
            for job in package.jobs.get("completed_jobs", []):
                print(f"✓ {job.job_file_info.table_name}: loaded")
    except Exception as e:
        print(json.dumps({"level": "ERROR", "pipeline": "faker_file", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Critical Implementation Rules

**Pipeline and dataset naming — must align with sources.yml:**
- `pipeline_name="faker_file"` — matches the dbt source name `faker_file` declared in `models/bronze/sources.yml`
- `dataset_name="bronze"` — writes to the `bronze` DuckDB schema (same schema dbt reads via `{{ source() }}`)
- The DuckDB file must be `dev.duckdb` (the same file dbt uses) — read from `DBT_DUCKDB_PATH`

**write_disposition="merge" is mandatory:**
- `"append"` would duplicate rows on every run — AC3 would fail
- `"replace"` would truncate and reload — not idempotent in the true sense
- `"merge"` with `primary_key` deduplicates: same UUID on second run = upsert, not insert

**Bronze metadata boundary (critical architectural rule):**
- dlt automatically adds `_dlt_load_id` (load batch ID) and `_dlt_id` (row content hash) to every table
- Do NOT manually add `_loaded_at` or `_source` to Bronze — these belong in Silver (Story 2.4)
- Do NOT rename `_dlt_load_id` or `_dlt_id` — they must match what `sources.yml` declared in Story 2.1

**DuckDB also receives dlt internal tables:**
- dlt writes `_dlt_pipeline_state` and `_dlt_loads` tables into the `bronze` schema
- These are expected — AC4 says "only dlt-written tables" which includes these internal tables
- Silver models (Story 2.4) will read from `customers`, `products`, `orders`, `returns` only — not the dlt internal tables

### Prerequisite: data/ files must exist

The pipeline reads from `data/customers.json`, `data/products.json`, `data/orders.json`, `data/returns.json`. Run `python ingest/faker_generator.py` first if these files are absent (they are gitignored and not committed).

```bash
python ingest/faker_generator.py   # generates data/*.json
python ingest/dlt_file_source.py   # loads to bronze schema
```

### Verifying Bronze Tables in DuckDB

After running the pipeline, verify with DuckDB CLI or in Python:

```python
import duckdb
conn = duckdb.connect("dev.duckdb")

# List all schemas
conn.execute("SELECT schema_name FROM information_schema.schemata").fetchall()
# Should include 'bronze'

# List bronze tables
conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'bronze'").fetchall()
# Should include customers, products, orders, returns (plus dlt internal tables)

# Check columns — _dlt_load_id and _dlt_id must be present
conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'bronze' AND table_name = 'customers'").fetchall()

# Row counts
conn.execute("SELECT COUNT(*) FROM bronze.customers").fetchone()
```

### sources.yml Already Updated

`models/bronze/sources.yml` was fully populated in Story 2.1 with all 4 entity schemas including `_dlt_load_id` and `_dlt_id` column declarations. Do NOT modify it in this story — it will be validated against actual dlt table structures in Story 2.4.

### Error Handling Pattern (consistent with faker_generator.py)

```python
except Exception as e:
    print(json.dumps({"level": "ERROR", "pipeline": "faker_file", "error": str(e)}))
    sys.exit(1)
```

This follows the same pattern as `faker_generator.py` from Story 2.1 — structured JSON error to stdout, exit code 1 so Makefile/cron detect failures (Story 2.12 wires these together).

### Story Scope Boundaries

**IN SCOPE:**
- `ingest/dlt_file_source.py` — the dlt pipeline script

**OUT OF SCOPE:**
- `ingest/dlt_api_source.py` → Story 2.3
- Silver dbt models → Story 2.4
- `make run-pipeline` / `make load-data` Makefile targets → Story 2.12
- Any modification to `models/bronze/sources.yml` (done in 2.1)
- Any modification to `dbt_project.yml`
- Root `requirements.txt` (ingest/ has its own)

**DO NOT:**
- Add `_loaded_at` or `_source` to Bronze tables — Silver-layer metadata only
- Create any `.sql` file under `models/bronze/` — Bronze is dlt-owned
- Change `write_disposition` to `"append"` — breaks AC3 deduplication

### Previous Story Context (2.1)

From Story 2.1:
- `ingest/requirements.txt` already contains `dlt>=0.4.0` — no new packages needed
- `data/*.json` files are generated by `faker_generator.py` and gitignored
- `models/bronze/sources.yml` is fully populated with all 4 entity schemas
- `DBT_DUCKDB_PATH=dev.duckdb` is already in `.env.example`
- `FAKER_OUTPUT_DIR=data` is already in `.env.example`
- pyenv Python on this machine requires `REQUESTS_CA_BUNDLE=/tmp/system-certs.pem` for outbound HTTPS (dbt hub) — not relevant for dlt which doesn't make outbound calls beyond PyPI install

### FR/NFR Coverage

| Requirement | Implementation |
|---|---|
| FR8 | dlt file source → Bronze |
| FR11 | Bronze immutability — no modification of source values |
| FR12 | Ingestion metadata stamping — `_dlt_load_id`, `_dlt_id` present |
| NFR16 | Idempotency — merge disposition, same data = same row count |

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

- `ingest/dlt_file_source.py` (created)

## Change Log

- 2026-03-31: Story 2.2 created — dlt file source ingestion to bronze.
