# Story 2.3: dlt API Source Ingestion to Bronze

Status: done

## Story

As a data engineer,
I want dlt to ingest data from a REST API source into the Bronze layer,
So that I experience both file-based and API-based ingestion patterns in a single pipeline.

## Acceptance Criteria

1. **Given** `API_BASE_URL` is set (default: `https://jsonplaceholder.typicode.com`), **When** I run `python ingest/dlt_api_source.py`, **Then** `posts` and `users` tables land in the `bronze` schema in `dev.duckdb` — `_dlt_load_id` and `_dlt_id` present on both tables, all scalar source columns present with correct types.

2. **Given** the pipeline errors (e.g. endpoint unreachable, HTTP 4xx/5xx), **When** the exception occurs, **Then** the error is logged to stdout as `{"level": "ERROR", "pipeline": "jsonplaceholder", "error": "..."}` and the script exits with code 1.

3. **Given** I run the pipeline twice on the same endpoint, **When** I count Bronze rows after each run, **Then** row count does not increase — dlt deduplicates using `id` as the primary key with `write_disposition="merge"`.

4. **Given** `models/bronze/sources.yml`, **When** I inspect it, **Then** a `jsonplaceholder` source is declared with `posts` and `users` tables including `_dlt_load_id` and `_dlt_id` columns — this forward-declares the schema for Story 2.4+ reference.

## Tasks / Subtasks

- [x] Task 1: Create `ingest/dlt_api_source.py` (AC: 1, 2, 3)
  - [x] Read `API_BASE_URL` env var (default: `https://jsonplaceholder.typicode.com`)
  - [x] Read `DBT_DUCKDB_PATH` env var (default: `dev.duckdb`)
  - [x] Create dlt pipeline: `pipeline_name="jsonplaceholder"`, DuckDB destination at `DBT_DUCKDB_PATH`, `dataset_name="bronze"`
  - [x] Define `posts` resource: `@dlt.resource(name="posts", primary_key="id", write_disposition="merge")` — GET `{API_BASE_URL}/posts`
  - [x] Define `users` resource: `@dlt.resource(name="users", primary_key="id", write_disposition="merge")` — GET `{API_BASE_URL}/users`
  - [x] Each resource: `requests.get(url, timeout=30)`, call `raise_for_status()` before yielding
  - [x] Wrap pipeline run in try/except — on failure print structured JSON and exit 1
  - [x] Print per-table row count on success: `✓ posts: N rows`, `✓ users: N rows` (query DuckDB directly, same pattern as dlt_file_source.py)
  - [x] VERIFY: `python ingest/dlt_api_source.py` — no errors, `posts` and `users` tables in `bronze` schema
  - [x] VERIFY: `_dlt_load_id` and `_dlt_id` present on both tables
  - [x] VERIFY: No extra metadata columns (`_loaded_at`, `_source`) in Bronze tables

- [x] Task 2: Add `requests` to `ingest/requirements.txt` (AC: 1)
  - [x] Add `requests>=2.31.0` to `ingest/requirements.txt`

- [x] Task 3: Add `API_BASE_URL` to `.env.example` (AC: 1)
  - [x] Append `API_BASE_URL=https://jsonplaceholder.typicode.com` with a comment under the Faker section

- [x] Task 4: Update `models/bronze/sources.yml` — add `jsonplaceholder` source (AC: 4)
  - [x] Add second source block `name: jsonplaceholder`, `schema: bronze`, `description` matching the pattern in the file
  - [x] Declare `posts` table: columns `id`, `user_id`, `title`, `body`, `_dlt_load_id`, `_dlt_id`
  - [x] Declare `users` table: columns `id`, `name`, `username`, `email`, `phone`, `website`, `_dlt_load_id`, `_dlt_id`
  - [x] Note in description that dlt flattens nested `address__*` and `company__*` fields into columns (not declared here — not referenced by Silver models)
  - [x] VERIFY: `dbt compile` succeeds after sources.yml update

- [x] Task 5: Verify idempotency (AC: 3)
  - [x] Run pipeline twice on the same endpoint
  - [x] VERIFY: Row counts in `bronze.posts` and `bronze.users` identical after both runs

- [x] Task 6: Final AC check
  - [x] AC1: `posts` (100 rows) and `users` (10 rows) in bronze; `_dlt_load_id` and `_dlt_id` present
  - [x] AC2: Confirm error path works — temporarily set `API_BASE_URL=http://localhost:9999` and verify structured JSON + exit 1
  - [x] AC3: Second run — row counts unchanged
  - [x] AC4: `sources.yml` declares `jsonplaceholder` source with both tables

### Review Findings

- [x] [Review][Patch] Runtime env-var functions instead of module-level constants — inconsistent with `dlt_file_source.py`; `get_duckdb_path()` called twice (pipeline config + verify connection) [`ingest/dlt_api_source.py`]
- [x] [Review][Patch] `pipeline.run()` return value discarded — dlt partial-load failures (failed jobs) produce silent exit 0 with row counts printed [`ingest/dlt_api_source.py`]
- [x] [Review][Patch] `API_BASE_URL` not stripped of trailing slash — `https://example.com/` produces `https://example.com//posts` [`ingest/dlt_api_source.py`]
- [x] [Review][Defer] SQL injection f-string in table-name loop [`ingest/dlt_api_source.py`] — deferred, pre-existing pattern in `dlt_file_source.py`
- [x] [Review][Defer] DuckDB verify block shares outer try/except with pipeline run [`ingest/dlt_api_source.py`] — deferred, pre-existing pattern in `dlt_file_source.py`

## Dev Notes

### API Choice: JSONPlaceholder

JSONPlaceholder (`https://jsonplaceholder.typicode.com`) is used as the demo API. It is:
- Free, no API key required
- Reliable and well-known in tutorial contexts
- Returns deterministic datasets (100 posts, 10 users — same every call)

This is intentionally different data from the Faker e-commerce entities — it demonstrates that a production platform ingests from multiple source systems. The `posts` and `users` tables are **not referenced by Silver models** (Story 2.4 reads from `faker_file` source only); they exist in Bronze for pattern demonstration.

**Entities:**
- `GET /posts` → 100 records: `{id, userId, title, body}` — dlt writes as `{id, user_id, title, body}` (snake_case)
- `GET /users` → 10 records: `{id, name, username, email, phone, website, address{...}, company{...}}`

**dlt flattening behaviour:**
dlt flattens nested JSON objects into columns with `__` separator: `address.city` → `address__city`. For `users`, expect columns like `address__city`, `address__zipcode`, `company__name`, etc. These are NOT declared in `sources.yml` because Silver models do not reference them — but they will be present in `bronze.users`.

### Implementation Pattern

Follow the exact same structure as `ingest/dlt_file_source.py`. Key differences:
- `pipeline_name="jsonplaceholder"` (not `"faker_file"`)
- HTTP GET via `requests` instead of file reads
- `TABLES = ["posts", "users"]` for the success output loop

```python
#!/usr/bin/env python3
"""
dlt API source pipeline for local-data-platform.
Reads from JSONPlaceholder REST API and loads to bronze schema in DuckDB.

Usage:
    python ingest/dlt_api_source.py
    API_BASE_URL=https://jsonplaceholder.typicode.com DBT_DUCKDB_PATH=dev.duckdb python ingest/dlt_api_source.py
"""
import json
import os
import sys

import dlt
import duckdb
import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "https://jsonplaceholder.typicode.com")
DUCKDB_PATH = os.environ.get("DBT_DUCKDB_PATH", "dev.duckdb")

TABLES = ["posts", "users"]


@dlt.resource(name="posts", primary_key="id", write_disposition="merge")
def posts():
    resp = requests.get(f"{API_BASE_URL}/posts", timeout=30)
    resp.raise_for_status()
    yield resp.json()


@dlt.resource(name="users", primary_key="id", write_disposition="merge")
def users():
    resp = requests.get(f"{API_BASE_URL}/users", timeout=30)
    resp.raise_for_status()
    yield resp.json()


@dlt.source
def jsonplaceholder_source():
    yield posts()
    yield users()


def main():
    try:
        pipeline = dlt.pipeline(
            pipeline_name="jsonplaceholder",
            destination=dlt.destinations.duckdb(DUCKDB_PATH),
            dataset_name="bronze",
        )
        pipeline.run(jsonplaceholder_source())
        conn = duckdb.connect(DUCKDB_PATH, read_only=True)
        for table in TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM bronze.{table}").fetchone()[0]
            print(f"✓ {table}: {count} rows")
        conn.close()
    except Exception as e:
        print(json.dumps({"level": "ERROR", "pipeline": "jsonplaceholder", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Critical Implementation Rules

**pipeline_name must be `"jsonplaceholder"`:**
- This is what the dbt source declaration `name: jsonplaceholder` in `sources.yml` refers to
- Do NOT use `"faker_api"` — the source name must match the pipeline name

**write_disposition="merge" is mandatory:**
- JSONPlaceholder returns the same data every call — `"append"` would duplicate rows on every run
- `primary_key="id"` (integer) — same as the JSONPlaceholder `id` field

**`requests.raise_for_status()` before yield:**
- HTTP 4xx/5xx errors must surface as exceptions so the try/except catches them
- `timeout=30` prevents the script hanging if the endpoint is slow

**Do NOT add `_loaded_at` or `_source` to Bronze:**
- Same rule as dlt_file_source.py — Silver-layer metadata only (Story 2.4)

**Per-table row count pattern (learned from Story 2.2 review):**
- Print row counts after successful run — same DuckDB query pattern used in dlt_file_source.py
- Use `TABLES = ["posts", "users"]` constant for the loop

### sources.yml Addition

Add a second source block to `models/bronze/sources.yml`. Append AFTER the existing `faker_file` source block:

```yaml
  - name: jsonplaceholder
    description: "JSONPlaceholder public REST API data loaded to Bronze by dlt (Story 2.3). Posts and users only — not referenced by Silver models."
    schema: bronze
    tables:
      - name: posts
        description: "JSONPlaceholder posts — 100 records, fixed dataset"
        columns:
          - name: id
            description: "Post primary key (integer)"
            data_type: bigint
            meta: {pii: false}
          - name: user_id
            description: "FK to users.id (dlt snake_cases userId → user_id)"
            data_type: bigint
            meta: {pii: false}
          - name: title
            description: "Post title"
            data_type: varchar
            meta: {pii: false}
          - name: body
            description: "Post body text"
            data_type: varchar
            meta: {pii: false}
          - name: _dlt_load_id
            description: "dlt load batch identifier"
            data_type: varchar
            meta: {pii: false}
          - name: _dlt_id
            description: "dlt row-level hash"
            data_type: varchar
            meta: {pii: false}

      - name: users
        description: "JSONPlaceholder users — 10 records. Nested address/company fields are dlt-flattened into address__* and company__* columns (not declared here)."
        columns:
          - name: id
            description: "User primary key (integer)"
            data_type: bigint
            meta: {pii: false}
          - name: name
            description: "Full name — PII"
            data_type: varchar
            meta: {pii: true}
          - name: username
            description: "Username handle"
            data_type: varchar
            meta: {pii: false}
          - name: email
            description: "Email address — PII"
            data_type: varchar
            meta: {pii: true}
          - name: phone
            description: "Phone number — PII"
            data_type: varchar
            meta: {pii: true}
          - name: website
            description: "Personal website URL"
            data_type: varchar
            meta: {pii: false}
          - name: _dlt_load_id
            description: "dlt load batch identifier"
            data_type: varchar
            meta: {pii: false}
          - name: _dlt_id
            description: "dlt row-level hash"
            data_type: varchar
            meta: {pii: false}
```

### .env.example Addition

Append under the `# Faker synthetic data generator` section:

```
# dlt API source (Story 2.3)
# Base URL for the REST API endpoint used by dlt_api_source.py
API_BASE_URL=https://jsonplaceholder.typicode.com
```

### Verifying Bronze Tables

After running the pipeline:

```python
import duckdb
conn = duckdb.connect("dev.duckdb")

# Confirm posts and users exist
conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'bronze'").fetchall()

# Check row counts
conn.execute("SELECT COUNT(*) FROM bronze.posts").fetchone()   # → (100,)
conn.execute("SELECT COUNT(*) FROM bronze.users").fetchone()   # → (10,)

# Confirm dlt columns present
conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='bronze' AND table_name='posts'").fetchall()
```

### Error Path Verification (AC2)

To verify the error handler works:
```bash
API_BASE_URL=http://localhost:9999 python ingest/dlt_api_source.py
```
Expected output: `{"level": "ERROR", "pipeline": "jsonplaceholder", "error": "..."}` and exit code 1 (verify with `echo $?`).

### Prerequisite

`dev.duckdb` must exist (created by the dlt_file_source.py pipeline in Story 2.2 or by running `dbt compile`). Both pipelines write to the same `bronze` schema in the same DuckDB file.

### Story Scope Boundaries

**IN SCOPE:**
- `ingest/dlt_api_source.py` (created)
- `ingest/requirements.txt` (add `requests>=2.31.0`)
- `.env.example` (add `API_BASE_URL`)
- `models/bronze/sources.yml` (add `jsonplaceholder` source block)

**OUT OF SCOPE:**
- Silver dbt models → Story 2.4
- `make run-pipeline` → Story 2.12
- Any modification to `dbt_project.yml`
- Any `.sql` file under `models/bronze/`
- Pagination, authentication, or incremental loading patterns (not required for JSONPlaceholder)

**DO NOT:**
- Add `_loaded_at` or `_source` to Bronze tables
- Use `write_disposition="append"` — breaks idempotency
- Rename `_dlt_load_id` or `_dlt_id`

### Previous Story Context (2.2)

From Story 2.2:
- `ingest/requirements.txt` has `dlt>=0.4.0` — do not remove, add `requests>=2.31.0` alongside
- dlt 1.24.0 is installed — requires `pydantic>=2.6.0` (already in environment)
- dlt writes `_dlt_loads`, `_dlt_pipeline_state`, `_dlt_version` internal tables to `bronze` — expected, not bugs
- The `duckdb.connect(DUCKDB_PATH, read_only=True)` pattern for post-run row counts works correctly
- `pipeline.run()` returns `LoadInfo` — not needed for output; query DuckDB directly for row counts

### FR/NFR Coverage

| Requirement | Implementation |
|---|---|
| FR9 | dlt API source → Bronze |
| FR11 | Bronze immutability — no modification of source values |
| FR12 | Ingestion metadata stamping — `_dlt_load_id`, `_dlt_id` present |
| NFR16 | Idempotency — merge disposition, same data = same row count |

## Dev Agent Record

### Agent Model Used

Codex GPT-5

### Debug Log References

- `python3 -m unittest discover -s tests`
- `python3 ingest/dlt_api_source.py`
- `API_BASE_URL=http://localhost:9999 python3 ingest/dlt_api_source.py`
- `dbt compile --profiles-dir .`

### Completion Notes List

- Implemented `ingest/dlt_api_source.py` with `posts` and `users` dlt resources, runtime env-var lookup, structured JSON error handling, and post-load Bronze row-count summaries.
- Added `requests>=2.31.0` to `ingest/requirements.txt` and documented `API_BASE_URL` in `.env.example`.
- Extended `models/bronze/sources.yml` with a forward-declared `jsonplaceholder` source for `posts` and `users`, including dlt metadata columns and note about flattened nested fields.
- Added `unittest` coverage for API fetch behavior, structured failure handling, and idempotent merge loading into DuckDB.
- Validated live ingestion against JSONPlaceholder: `posts=100`, `users=10`, `_dlt_load_id` and `_dlt_id` present, no `_loaded_at` or `_source` columns, and repeat run preserved row counts.
- Addressed review follow-ups: normalized `API_BASE_URL`, resolved config once in `main`, and now fail explicitly on partial dlt load jobs via `load_info.raise_on_failed_jobs()`.
- Expanded tests to cover trailing-slash normalization and isolated the structured-error test from the shared DuckDB file.

### File List

- `ingest/dlt_api_source.py` (created)
- `ingest/__init__.py` (created)
- `ingest/requirements.txt` (modified — added requests)
- `.env.example` (modified — added API_BASE_URL)
- `models/bronze/sources.yml` (modified — added jsonplaceholder source)
- `tests/test_dlt_api_source.py` (created)

## Change Log

- 2026-03-31: Story 2.3 created — dlt API source ingestion to bronze.
- 2026-03-31: Implemented JSONPlaceholder API ingestion to Bronze, added source declarations/config, and validated success, error handling, and idempotency. 
- 2026-03-31: Addressed code review findings for story 2.3 — normalized API base URL handling, validated dlt load failures, and updated test coverage.
