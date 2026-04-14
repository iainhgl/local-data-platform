# Epic 2 — Simple Profile: First Working Pipeline

This document summarises everything built in Epic 2. By the end of Epic 2 you have a fully working local data platform running on a single machine: synthetic data is generated and ingested on a schedule, transformed through a medallion architecture, tested, observed, and served through multiple BI and reporting interfaces.

---

## What was built

### Data generation and ingestion

Two ingestion scripts load data into a **Bronze layer** (raw, append-only) inside DuckDB:

| Script | What it does |
|---|---|
| `ingest/faker_generator.py` | Generates synthetic JSON files in `data/` — customers, products, orders, returns |
| `ingest/dlt_file_source.py` | Reads those JSON files using dlt, writes to `bronze.faker_*` tables in DuckDB |
| `ingest/dlt_api_source.py` | Calls the [JSONPlaceholder](https://jsonplaceholder.typicode.com) REST API using dlt, writes to `bronze.api_*` tables |

Both ingest scripts use [dlt](https://dlthub.com) for schema inference, incremental loading, and load metadata tracking.

### dbt transformation layers (medallion architecture)

All transformation runs on the host via dbt Core targeting `dev.duckdb`.

```
Bronze (raw)  →  Silver (cleaned)  →  Gold (analytics-ready)
                     ↓
               Quarantine (failed records)
```

**Silver** (`models/silver/faker/`) — four incremental models, one per entity:

- `faker_customers` — deduplicated, typed, PII-flagged
- `faker_products` — price/quantity normalised
- `faker_orders` — FK-validated, status-normalised, total_amount derived
- `faker_returns` — FK-validated, reason-normalised

**Quarantine** (`models/quarantine/faker/`) — failed records split off from Silver using CASE/WHERE logic; stored in a separate DuckDB schema so bad data is visible and auditable without polluting Silver.

**Gold** (`models/gold/`) — analytics-ready layer for BI and reporting:

| Model | Type | Description |
|---|---|---|
| `dim_customers` | Dimension | SCD-ready customer attributes |
| `dim_products` | Dimension | Product catalogue with price tiers |
| `fct_orders` | Fact | Order grain — revenue, status, FK references |
| `orders_mart` | Mart | Denormalised orders with customer name and product name joined in |

### MetricFlow semantic layer

Defined in `models/metrics/`:

| File | Metrics defined |
|---|---|
| `orders.yml` | `order_count`, `revenue` — with time dimension (`order_date`), categorical dimensions (`order_status`, `has_return`) |
| `customers.yml` | `customer_count` — with time dimension (`first_order_date`), categorical dimension (`customer_state`) |
| `time_spine.sql` | Required MetricFlow calendar spine (daily granularity) |

Metrics are queryable via `dbt sl query` and will power the MCP Server in Story 5.5.

### Data quality

Managed in `models/silver/faker/schema.yml` and `models/gold/*/schema.yml` using dbt Core tests and [dbt-expectations](https://github.com/calogica/dbt-expectations):

- `not_null` and `unique` on all primary keys
- `accepted_values` on status and categorical columns
- `expect_column_values_to_be_between` on numeric ranges
- Source freshness checks on Bronze tables

Run with `dbt test` (included in `make run-pipeline`).

### Observability — Elementary

[Elementary](https://docs.elementary-data.com) runs as a post-pipeline step:

```bash
edr report --profiles-dir . --profile-target elementary
```

This generates `edr_target/elementary_report.html` — a full data observability report covering test results, model run history, and anomaly detection. Served by the `elementary` Docker container at `http://localhost:18030/elementary_report.html`.

### Analytical reports — Evidence

[Evidence](https://evidence.dev) provides a code-driven reporting layer. Reports are Markdown files with embedded SQL:

- `evidence/pages/index.md` — landing page
- `evidence/pages/gold/orders-summary.md` — orders summary dashboard (revenue trends, status breakdown)

Evidence builds against the DuckDB file using its DuckDB connector. The build runs **on the host** (not in Docker) because DuckDB's WASM bundling requires macOS:

```bash
make build-evidence
```

The pre-built output is then served by the `evidence` Docker container at `http://localhost:18010`.

### dbt docs and column lineage

`dbt docs generate` produces `target/catalog.json` and `target/index.html` — a full documentation site with:

- Model descriptions and column-level metadata from `schema.yml`
- Automatic column lineage derived from `{{ ref() }}` and `{{ source() }}` calls
- DAG visualisation of the full model graph

Served by the `dbt-docs` Docker container at `http://localhost:18020`.

### Cron scheduler

The `cron-scheduler` Docker service runs the pipeline automatically on a configurable interval (default: 1 hour). It uses a custom Docker image (`docker/scheduler/Dockerfile`) containing dbt-duckdb, dlt, Faker, and the ingest scripts.

Each scheduled run executes:

1. `dlt_file_source.py` — file ingestion
2. `dlt_api_source.py` — API ingestion
3. `dbt run` — transform all layers
4. `dbt test` — run all quality tests
5. `dbt docs generate` — regenerate documentation

Evidence build and Elementary report are excluded from the scheduler (both require host-native tools or macOS ARM64 compatibility); run them manually with `make run-pipeline` or `make build-evidence`.

---

## How to run it

### Prerequisites

- Docker Desktop (with Compose v2)
- Python 3.11+
- dbt-duckdb: `pip install dbt-duckdb`
- dlt: `pip install "dlt[filesystem]"`
- Node.js 20+ (for Evidence build)
- 8 GB RAM minimum

### First-time setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/iainhgl/local-data-platform.git
cd local-data-platform

# 2. Install dbt packages
make install

# 3. Copy and review environment config
cp .env.example .env
# Default values work out of the box for the simple profile — no changes required

# 4. Start Docker services (simple profile by default)
make start

# 5. Run the pipeline (generates data, runs dbt, builds all docs)
make run-pipeline

# 6. Open all dashboards in your browser
make open-docs
```

### Subsequent runs

The cron scheduler runs the pipeline automatically every hour. For a manual run:

```bash
make run-pipeline
```

To stop all services:

```bash
make stop
```

### Disabling the scheduler

Set `CRON_INTERVAL=0` in `.env` then restart:

```bash
make stop && make start
```

The scheduler container starts but sleeps indefinitely — pipeline only runs when you call `make run-pipeline` manually.

---

## How to verify it is working

### 1. Check Docker services are up

```bash
docker compose ps
```

All services (`evidence`, `dbt-docs`, `elementary`, `cron-scheduler`, `lightdash`, `lightdash-db`) should show `Up`.

### 2. Check the pipeline ran

After `make run-pipeline`, look for this in terminal output:

```
✔  Pipeline complete — run make open-docs to view dashboards
```

And check the DuckDB file exists:

```bash
ls -lh dev.duckdb
```

### 3. Query the data directly

```bash
duckdb dev.duckdb
```

```sql
-- Check Bronze loaded
SELECT COUNT(*) FROM bronze.faker_customers__data;

-- Check Silver transformed
SELECT COUNT(*) FROM silver.faker_customers;
SELECT COUNT(*) FROM silver.faker_orders;

-- Check Gold ready
SELECT COUNT(*) FROM gold.fct_orders;
SELECT SUM(total_amount) AS total_revenue FROM gold.fct_orders;

-- Check Quarantine captured failed records
SELECT COUNT(*) FROM quarantine.faker_orders_failed;
```

### 4. Check dbt test results

```bash
dbt test
```

All tests should pass. Any failures are surfaced with the model name and test type.

### 5. Open the dashboards

```bash
make open-docs
```

| Dashboard | URL | What to check |
|---|---|---|
| Evidence reports | http://localhost:18010 | Orders summary report — revenue chart, status breakdown |
| dbt docs | http://localhost:18020 | Model DAG, column lineage, schema descriptions |
| Elementary | http://localhost:18030/elementary_report.html | Test pass/fail history, model run durations |
| Lightdash | http://localhost:18000 | Loads (DuckDB adapter pending; full support in Story 3.4) |

### 6. Check the scheduler is running

```bash
docker logs local-data-platform-cron-scheduler-1 --tail 50
```

You should see:

```
▶  Scheduler starting - interval: 3600s
▶  [cron] Running ingestion (file source)...
▶  [cron] Running ingestion (API source)...
▶  [cron] Running dbt run...
▶  [cron] Running dbt test...
▶  [cron] Generating dbt docs...
✔  [cron] Pipeline complete at <timestamp>
```

### 7. Verify MetricFlow

```bash
dbt sl list metrics
dbt sl query --metrics order_count --group-by order_date__day
```

---

## Key configuration

All configuration lives in `.env`. The defaults work for the simple profile without changes.

| Variable | Default | Description |
|---|---|---|
| `COMPOSE_PROFILES` | `simple` | Active profile — controls which Docker services start |
| `DBT_DUCKDB_PATH` | `dev.duckdb` | Path to the DuckDB file (relative to repo root) |
| `FAKER_ROWS` | `1000` | Rows per entity generated by Faker |
| `FAKER_OUTPUT_DIR` | `data` | Output directory for Faker JSON files |
| `API_BASE_URL` | `https://jsonplaceholder.typicode.com` | REST API endpoint for dlt API source |
| `CRON_INTERVAL` | `3600` | Scheduler interval in seconds (0 = disabled) |
| `LIGHTDASH_SECRET` | `changeme-...` | Session signing secret for Lightdash |

---

## Architecture diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Data Sources                                                    │
│  faker_generator.py → data/*.json   JSONPlaceholder REST API    │
└────────────────┬────────────────────────────┬───────────────────┘
                 │ dlt (file source)           │ dlt (API source)
                 ▼                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Bronze layer (DuckDB)                                           │
│  bronze.faker_customers__data   bronze.faker_orders__data  ...  │
│  bronze.api_posts__data         bronze.api_users__data     ...  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ dbt incremental models
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Silver layer (DuckDB)                   Quarantine (DuckDB)    │
│  silver.faker_customers                  quarantine.*_failed    │
│  silver.faker_products                                          │
│  silver.faker_orders                                            │
│  silver.faker_returns                                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │ dbt models
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Gold layer (DuckDB)                                            │
│  gold.dim_customers   gold.dim_products                         │
│  gold.fct_orders      gold.orders_mart                          │
└──────┬──────────┬──────────────┬───────────────────────────────┘
       │          │              │
       ▼          ▼              ▼
  MetricFlow   Evidence      dbt docs
  semantic      reports      + lineage
  layer         (18010)        (18020)
       │
  (dbt sl query / Story 5.5 MCP)

Observability: Elementary (18030) — runs after every pipeline

Scheduling: cron-scheduler container (simple profile) — every CRON_INTERVAL seconds
```

---

## Known limitations (deferred to later epics)

- **DuckDB write lock**: Only one process can write to `dev.duckdb` at a time. If the cron-scheduler is mid-run and you call `make run-pipeline` from the host, the second opener receives `IOException: Could not set lock on file`. Workaround: set `CRON_INTERVAL=0` when doing manual development runs.
- **Evidence build on macOS only**: DuckDB's WASM bundler hangs inside a Linux ARM64 Docker container. The build must run on the macOS host (`make build-evidence`). On Linux hosts, run `npm run build` directly inside the `evidence/` directory.
- **Lightdash DuckDB support**: Lightdash's local DuckDB adapter is not yet released upstream. The service starts but cannot connect to `dev.duckdb`. Full Lightdash support is in Story 3.4 (Postgres profile).
- **Elementary opens at directory listing**: `make open-docs` opens `http://localhost:18030/` which shows a directory listing. Navigate to `http://localhost:18030/elementary_report.html` directly.
- **No version pinning in scheduler Dockerfile**: `docker/scheduler/Dockerfile` installs the latest versions of dbt-duckdb, dlt, and Faker. Pin versions before using this in any stable environment.
