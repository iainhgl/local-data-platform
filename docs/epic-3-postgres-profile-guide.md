# Epic 3 — Postgres Profile: Manual Validation Guide

This guide walks you through switching to the Postgres profile and manually validating everything built in Epic 3. Work through it in order — each section builds on the previous one.

---

## What was built

| Story | What it adds |
|---|---|
| 3.1 | Postgres container, schemas, three RBAC roles, profile-aware dbt + ingestion |
| 3.2 | PII masking views for analyst_role, pii_access_log, Makefile pipeline integration |
| 3.3 | dbt schema contracts (`constraints:`) on all Gold models, fail-fast on schema drift |
| 3.4 | Lightdash BI dashboard wired to the Postgres Gold schema |

---

## Prerequisites

### 1. Install the Postgres dbt adapter on the host

```bash
pip install dbt-postgres==1.10.0
```

> `dbt-duckdb` and `dbt-postgres` can coexist. The active adapter is selected by the `--target` flag (or `profiles.yml` default), not by which package is installed.

### 2. Install psycopg2 (if not already installed)

```bash
pip install -r requirements.txt
```

This installs `psycopg2-binary`, which the ingest scripts use to verify Postgres row counts.

---

## Step 1: Switch to the Postgres profile

Edit `.env` and set:

```
COMPOSE_PROFILES=postgres
```

### Force a clean Postgres container start

The Postgres Docker image only runs init scripts (`docker/init/postgres_init.sql`) on first start when the data directory is empty. If you have run the platform before, you must reset the volume:

```bash
make stop
docker compose down -v    # removes the postgres data volume — dev only, destructive
make start
```

If this is a fresh clone (no existing volumes):

```bash
cp .env.example .env      # then set COMPOSE_PROFILES=postgres
make install              # installs dbt packages
make start
```

### Verify services are up

```bash
docker compose ps
```

Expected services running: `postgres`, `lightdash`, `lightdash-db`, `dbt-docs`, `evidence`, `elementary`.

> The `cron-scheduler` does **not** start on the postgres profile — orchestration is manual on this profile.

---

## Step 2: Validate Story 3.1 — Postgres profile and dbt adapter

### Check schemas and roles were created by the init script

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform -c "\dn"
```

Expected: `bronze`, `silver`, `gold`, `quarantine` schemas listed.

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform -c "\du"
```

Expected: `engineer_role`, `analyst_role`, `pii_analyst_role` roles listed.

### Run the pipeline against Postgres

```bash
make run-pipeline
```

This runs ingestion → `dbt run` → PII masking → `dbt test` → `dbt docs generate`. Elementary and Evidence are skipped automatically on the postgres profile (they are DuckDB-only components).

Expected output ends with:
```
✔  Pipeline complete — run make open-docs to view dashboards
```

### Query Postgres directly to confirm data loaded

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform -c "
    SELECT COUNT(*) AS bronze_customers FROM bronze.faker_customers__data;
    SELECT COUNT(*) AS silver_customers FROM silver.faker_customers;
    SELECT COUNT(*) AS gold_orders FROM gold.fct_orders;
    SELECT SUM(total_amount) AS total_revenue FROM gold.fct_orders;"
```

All four counts should be non-zero.

---

## Step 3: Validate Story 3.2 — RBAC and PII masking

All three commands below connect as the `dbt` superuser and then `SET ROLE` to simulate each persona. Run them in sequence.

### analyst_role sees redacted PII

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform \
  -c "SET ROLE analyst_role; SELECT customer_id, first_name, email FROM gold.dim_customers_masked LIMIT 3;"
```

Expected: `first_name` and `email` show `***REDACTED***`.

### analyst_role is denied on the base table

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform \
  -c "SET ROLE analyst_role; SELECT * FROM gold.dim_customers LIMIT 1;"
```

Expected: `ERROR: permission denied for table dim_customers`

### pii_analyst_role sees unmasked data

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform \
  -c "SET ROLE pii_analyst_role; SELECT customer_id, first_name, email FROM gold.dim_customers LIMIT 3;"
```

Expected: real customer names and email addresses.

### engineer_role has full access

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform \
  -c "SET ROLE engineer_role; SELECT customer_id, first_name FROM gold.dim_customers LIMIT 3;"
```

Expected: unmasked data, no permission error.

### Masked tables covered

Four PII-bearing tables have masking views applied:

| Base table | Masked view | PII columns redacted |
|---|---|---|
| `silver.faker_customers` | `silver.faker_customers_masked` | first_name, last_name, email, phone, address |
| `gold.dim_customers` | `gold.dim_customers_masked` | first_name, last_name, email, phone, address |
| `gold.orders_mart` | `gold.orders_mart_masked` | first_name, last_name, email |
| `quarantine.faker_customers_failed` | `quarantine.faker_customers_failed_masked` | first_name, last_name, email, phone, address |

### Demonstrate the PII access log

The `pii_access_log` table records manual entries. To demonstrate it:

```bash
docker exec $(docker compose ps -q postgres) \
  psql -U dbt -d local_data_platform -c "
    INSERT INTO public.pii_access_log (role_name, schema_name, table_name, query_text)
    VALUES ('pii_analyst_role', 'gold', 'dim_customers',
            'SELECT first_name, email FROM gold.dim_customers');
    SELECT logged_at, role_name, schema_name, table_name FROM public.pii_access_log;"
```

Or via Makefile:

```bash
make pg-show-pii-log
```

---

## Step 4: Validate Story 3.3 — dbt schema contracts

### Verify contract syntax compiles cleanly

```bash
make dbt-verify-contracts
```

This runs `dbt compile --select tag:gold` — validates all Gold model contracts without hitting the database. Expected: exits 0.

### Confirm contracts are enforced on a full run

Run the pipeline normally and confirm dbt run succeeds — the absence of a contract error is the passing condition:

```bash
dbt run --select tag:gold
```

Expected: all four Gold models (`fct_orders`, `dim_customers`, `dim_products`, `orders_mart`) materialise successfully.

### Demonstrate fail-fast on schema drift

This is the teaching moment for schema contracts. Temporarily break a contract to see how dbt reacts.

1. Open `models/gold/facts/schema.yml` and comment out the `order_id` column entry under `fct_orders`.
2. Run:
   ```bash
   dbt run --select fct_orders
   ```
3. Expected: the run fails with a contract violation error identifying the missing column.
4. Restore the file (`git checkout -- models/gold/facts/schema.yml`) and re-run to confirm it passes again.

### Check contracts declared in schema.yml

All four Gold models have `config: contract: enforced: true` and column-level `constraints:` on primary keys:

| Model | Constrained column | Types |
|---|---|---|
| `fct_orders` | `order_id` | not_null, primary_key |
| `dim_customers` | `customer_id` | not_null, primary_key |
| `dim_products` | `product_id` | not_null, primary_key |
| `orders_mart` | `order_id` | not_null, primary_key |

---

## Step 5: Validate Story 3.4 — Lightdash BI dashboard

### Ping Lightdash health

```bash
make lightdash-ping
```

Expected output:
```
✓ Lightdash healthy at http://localhost:18000
```

### Open Lightdash

```bash
open http://localhost:18000
```

Or navigate there manually. Lightdash requires an account on first run — create one locally (no external signup needed, local instance only).

### What to check in the UI

1. After logging in, navigate to **Explore** or **Tables**.
2. You should see explores derived from your Gold dbt models (`fct_orders`, `dim_customers`, `dim_products`, `orders_mart`).
3. Add a metric (e.g. `total_amount`) and a dimension (e.g. `order_date`) and run the query.
4. Check that results return and the SQL panel shows queries referencing the `gold` schema in Postgres.

> Lightdash reads your `dbt_project.yml`, `profiles.yml`, and `schema.yml` from the repo root (mounted into the container at `/workspace`). Model descriptions, column metadata, and `meta` tags you defined in `schema.yml` are surfaced directly in the Lightdash UI.

---

## Step 6: Run all tests

Run the full test suite to confirm no structural regressions:

```bash
python -m pytest tests/ -q
```

Story-specific test files:

| Test file | What it guards |
|---|---|
| `tests/test_story_3_1_postgres_profile.py` | Init SQL, compose config, profile-aware ingest scripts |
| `tests/test_story_3_2_rbac_pii_masking.py` | Masking SQL, all four REVOKE/VIEW/GRANT blocks, Makefile integration |
| `tests/test_story_3_3_schema_contracts.py` | Contract enforced on all Gold models, primary key constraints present |
| `tests/test_story_3_4_lightdash.py` | lightdash.config.yaml, compose volume mount, Makefile target |

---

## Switching back to the simple profile

```bash
# In .env, set:
COMPOSE_PROFILES=simple

make stop
make start
make run-pipeline    # runs full pipeline including Elementary and Evidence
```

No data migration required — DuckDB (`dev.duckdb`) and Postgres are separate stores. The dbt models are unchanged across both profiles.

---

## What does NOT run on the postgres profile

| Component | Status on postgres profile | Reason |
|---|---|---|
| cron-scheduler | Not started | postgres profile uses manual `make run-pipeline`; Airflow is Epic 5 |
| Elementary (`edr report`) | Skipped | Uses DuckDB-specific `elementary` dbt target; not configured for Postgres |
| Evidence build | Skipped | DuckDB WASM bundler; requires `make build-evidence` on simple profile |

---

## Key configuration (postgres profile)

All settings live in `.env`. These must be set for the postgres profile:

| Variable | Example value | Description |
|---|---|---|
| `COMPOSE_PROFILES` | `postgres` | Activates Postgres container and Lightdash data connection |
| `POSTGRES_HOST` | `localhost` | Host-side connection (container maps to 18040) |
| `POSTGRES_PORT` | `18040` | Host port for Postgres |
| `POSTGRES_USER` | `dbt` | Superuser created by Docker image |
| `POSTGRES_PASSWORD` | `changeme` | Set in `.env` — not committed |
| `POSTGRES_DB` | `local_data_platform` | Database name |
| `LIGHTDASH_SECRET` | `changeme-...` | Session signing secret for Lightdash |

The defaults in `.env.example` work out of the box for local development.
