# Story 2.13: dbt Documentation and Column Lineage

Status: done

## Story

As a data engineer,
I want dbt docs generated and served showing model descriptions, column lineage, and test coverage,
so that I can navigate the full transformation DAG and understand how data moves through the pipeline.

## Acceptance Criteria

1. **Given** `make run-pipeline` has completed, **When** I open `http://localhost:18020`, **Then** dbt docs are available within 30 seconds (NFR3).

2. **Given** dbt docs are open, **When** I navigate to a Gold model (e.g. `orders_mart`, `fct_orders`), **Then** column lineage traces back through Silver to Bronze source tables.

3. **Given** dbt docs are open, **When** I inspect any model or column, **Then** every node has a non-empty description — no undocumented models or columns appear (FR45, FR29, FR34).

## Tasks / Subtasks

- [x] Task 0: Create story branch
  - [x] `git checkout -b story/2-13-dbt-documentation-and-column-lineage`
  - [x] Confirm working tree is clean before starting

- [x] Task 1: Add `dbt docs generate` step to `make run-pipeline` (AC: 1, 2, 3)
  - [x] Open `Makefile`
  - [x] After the `dbt test` step and before the Elementary `edr report` step, add:
    ```makefile
    	@echo "▶  Generating dbt docs..."
    	@dbt docs generate
    ```
  - [x] VERIFY: run `make run-pipeline` end-to-end; confirm `target/catalog.json` and `target/index.html` are created in the repo root `target/` directory

- [x] Task 2: Update `dbt-docs` Docker service to serve the generated docs (AC: 1)
  - [x] Open `docker-compose.yml`
  - [x] Find the `dbt-docs:` service (currently port `18020:8080`, command `tail -f /dev/null`)
  - [x] Add a `volumes:` block mounting the host `target/` directory:
    ```yaml
        volumes:
          - "./target:/workspace/target"
    ```
  - [x] Change the `command:` from `tail -f /dev/null` to:
    ```yaml
        command: sh -c "python -m http.server 8080 --directory /workspace/target"
    ```
  - [x] VERIFY: `docker compose restart dbt-docs` (or full `make start`), then `curl -s -o /dev/null -w "%{http_code}" http://localhost:18020` returns `200`
  - [x] VERIFY: `open http://localhost:18020` shows the dbt docs UI in browser

- [x] Task 3: Confirm column lineage and full documentation coverage (AC: 2, 3)
  - [x] In the dbt docs UI, navigate to `gold` → `orders_mart`
  - [x] Click "See Lineage Graph" — confirm the DAG shows `bronze.faker_file.orders → silver.faker_orders → gold.fct_orders → gold.orders_mart` (and customers/products chains)
  - [x] In the docs UI, check that model descriptions are present on at least one model per layer: Bronze source, Silver, Gold, Quarantine
  - [x] No action required: all `schema.yml` files are already fully documented (see Dev Notes)

## Dev Notes

### What's Already Done — No Schema Changes Needed

All `schema.yml` / `sources.yml` files are **complete**. Every model and column already has a description and `data_type`. Do NOT add, remove, or reorganise any YAML declarations — the documentation is done.

| Layer | File | Status |
|-------|------|--------|
| Bronze | `models/bronze/sources.yml` | ✅ All sources, tables, columns documented |
| Silver | `models/silver/faker/schema.yml` | ✅ All 4 models + all columns documented |
| Gold facts | `models/gold/facts/schema.yml` | ✅ `fct_orders` fully documented |
| Gold dims | `models/gold/dimensions/schema.yml` | ✅ `dim_customers`, `dim_products` fully documented |
| Gold marts | `models/gold/marts/schema.yml` | ✅ `orders_mart` fully documented |
| Quarantine | `models/quarantine/faker/schema.yml` | ✅ All 4 failed models documented |
| Metrics | `models/metrics/schema.yml`, `orders.yml`, `customers.yml` | ✅ `time_spine`, semantic models documented |

### Why Column Lineage Works Without Code Changes

dbt generates lineage from `{{ ref() }}` and `{{ source() }}` calls in `.sql` files. Every Silver model already reads `{{ source('faker_file', 'customers') }}` etc., and every Gold model reads `{{ ref('faker_customers') }}` etc. Running `dbt docs generate` produces `target/catalog.json` which encodes this graph — no SQL or YAML changes are required.

### The Two Changes Required

**1. `Makefile` — add `dbt docs generate` after `dbt test`**

Current `run-pipeline` sequence:
```
ingestion (file) → ingestion (API) → dbt run → dbt test → edr report → build-evidence
```

Required:
```
ingestion (file) → ingestion (API) → dbt run → dbt test → dbt docs generate → edr report → build-evidence
```

Insert between the `dbt test` and `edr report` blocks. Follow the existing `@echo "▶  ..."` / `@dbt ...` two-line pattern. Do NOT change any other target.

**2. `docker-compose.yml` — wire dbt-docs service to serve `target/`**

The `dbt-docs` service comment says *"Story 2.13 completes dbt documentation and serving setup"* — it is an intentional placeholder. Follow the Elementary service pattern exactly:

```yaml
# Elementary (existing — pattern to copy)
  elementary:
    image: python:3.11-slim
    platform: linux/arm64
    volumes:
      - "./edr_target:/workspace/edr_target"
    command: sh -c "mkdir -p /workspace/edr_target && python -m http.server 8080 --directory /workspace/edr_target"

# dbt-docs (target state)
  dbt-docs:
    image: python:3.11-slim
    platform: linux/arm64
    profiles: ["simple", "postgres", "lakehouse", "full"]
    ports:
      - "18020:8080"
    volumes:
      - "./target:/workspace/target"
    command: sh -c "python -m http.server 8080 --directory /workspace/target"
    restart: unless-stopped
```

Note: `mkdir -p` guard is NOT needed for `target/` — dbt creates it on first `dbt run`. The directory already exists in this repo.

### `dbt docs generate` Output Files

Running `dbt docs generate` creates two files that `index.html` loads via AJAX:
- `target/catalog.json` — column types, row counts, table metadata (the key file for lineage + column docs)
- `target/index.html` — the single-page app that serves the docs UI

The `target/` directory already contains `manifest.json` and `sources.json` from prior `dbt run` / `dbt test` executions. `dbt docs generate` adds `catalog.json` and `index.html`.

### dbt Runs on Host, Not in Docker

`dbt run`, `dbt test`, and `dbt docs generate` all execute **on the host machine** (see `Makefile`). The Docker `dbt-docs` service only serves the pre-generated static files via `python -m http.server`. Never run dbt inside the container — dbt is not installed there.

### ZScaler Warning

Do NOT run `dbt deps` during validation — use existing `dbt_packages/` on disk. See `docs/troubleshooting-dbt-deps-zscaler-tls.md`. Run `dbt docs generate` directly without deps.

### Port Map

`18020:8080` — dbt docs (as declared in docker-compose.yml and README). Do not change the port.

### Files to Touch

| File | Change |
|------|--------|
| `Makefile` | Add `dbt docs generate` step in `run-pipeline` |
| `docker-compose.yml` | Add `volumes:` and update `command:` in `dbt-docs` service |

No other files need modification.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-04-10: Created branch `story/2-13-dbt-documentation-and-column-lineage`.
- 2026-04-10: Updated `Makefile` and `docker-compose.yml` per story instructions.
- 2026-04-10: Ran `make run-pipeline`, confirmed `target/catalog.json` and `target/index.html`, started `dbt-docs`, and verified HTTP `200` on `http://localhost:18020`.
- 2026-04-10: Validated lineage and documentation coverage from `target/manifest.json` for Bronze, Silver, Gold, and Quarantine resources.

### Completion Notes List

- Confirmed the repository was already dirty before starting because of pre-existing local changes in `.vscode/settings.json` and untracked workspace folders; development continued on the requested story branch without altering those files.
- `make run-pipeline` succeeded end-to-end after rerunning outside the sandbox for API network access, and `dbt docs generate` wrote `target/catalog.json` plus `target/index.html`.
- `docker compose up -d dbt-docs` succeeded and an out-of-sandbox `curl` to `http://localhost:18020` returned `200`.
- Verified lineage via `target/manifest.json`: `source.local_data_platform.faker_file.orders -> model.local_data_platform.faker_orders -> model.local_data_platform.fct_orders -> model.local_data_platform.orders_mart`.
- Verified documentation coverage via `target/manifest.json`: zero local models or sources had empty descriptions, and zero documented columns had empty descriptions.

### File List

- Makefile
- docker-compose.yml
- _bmad-output/implementation-artifacts/sprint-status.yaml
- _bmad-output/implementation-artifacts/2-13-dbt-documentation-and-column-lineage.md

### Change Log

- 2026-04-10: Added `dbt docs generate` to `make run-pipeline`, mounted `target/` into the `dbt-docs` service, and validated docs generation plus serving on port `18020`.

## Review Findings

- [x] [Review][Patch] Missing `mkdir -p` guard in dbt-docs command — container enters crash-restart loop on fresh clone where `target/` does not yet exist; Elementary service already uses this guard [docker-compose.yml] — FIXED: added `mkdir -p /workspace/target &&` to command
- [x] [Review][Patch] Stale comment in docker-compose.yml — line `# Served via 'dbt docs serve --port 18020'` contradicts the `python -m http.server` implementation now in place [docker-compose.yml] — FIXED: updated comment to describe actual serving mechanism
- [x] [Review][Defer] `run-pipeline` does not assert Docker services are running [Makefile] — deferred, pre-existing UX pattern; `make start` is the documented first step before `make run-pipeline`
- [x] [Review][Defer] Port `18020` binds on all host interfaces (`0.0.0.0`) [docker-compose.yml] — deferred, pre-existing across all services in the project; local dev tool by design
- [x] [Review][Defer] DuckDB exclusive write-lock on parallel `make run-pipeline` runs — deferred, pre-existing across all dbt commands; no serialisation mechanism exists in any pipeline target
- [x] [Review][Defer] No atomic swap for `catalog.json` on re-run — partially written file briefly served while pipeline re-runs; deferred, pre-existing pattern shared by Elementary and Evidence services
