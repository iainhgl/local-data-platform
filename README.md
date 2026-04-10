# local-data-platform

A self-contained, profile-switchable local data platform for learning modern data engineering patterns — dbt, dlt, DuckDB, Postgres, Iceberg/Trino, and more.

## Quick Start

1. **Clone the repo:**
   ```bash
   git clone https://github.com/iainhgl/local-data-platform.git
   cd local-data-platform
   ```
2. **Copy environment config:**
   ```bash
   cp .env.example .env
   ```
3. **Start services** (simple profile by default):
   ```bash
   make start
   ```
4. **Run the pipeline** (first run; subsequent runs are scheduled automatically):
   ```bash
   make run-pipeline
   ```
5. **Open dashboards:**
   ```bash
   make open-docs
   ```

> **Prerequisites:** Docker Desktop, Python 3.11+, dbt-duckdb, dlt - see [Hardware Requirements](#hardware-requirements) below.

## Profiles

Set `COMPOSE_PROFILES` in `.env` to switch profiles. All profiles share the same dbt models, ingestion scripts, and `schema.yml`.

| Profile | Query Engine | Use Case |
|---|---|---|
| `simple` | DuckDB (file-based) | Local learning - minimal footprint, no auth |
| `postgres` | Postgres (Docker) | Server warehouse, three-role RBAC, PII masking |
| `lakehouse` | Trino + MinIO + Iceberg | Open table formats, schema evolution, large datasets |
| `full` | All of the above | Enterprise stack - Airflow, Keycloak SSO, Superset, MCP |

See [docs/profile-guide.md](docs/profile-guide.md) for per-profile hardware and service details.

## Hardware Requirements

- **Minimum (simple / postgres profiles):** 8 GB RAM
- **Recommended (lakehouse / full profiles):** 16 GB RAM

## Cloud Equivalence

Every component maps to a cloud/SaaS equivalent. See [docs/cloud-equivalence.md](docs/cloud-equivalence.md) for the full table.

| Local | Cloud Equivalent |
|---|---|
| DuckDB | BigQuery Serverless / Redshift Serverless |
| dlt | Fivetran / Airbyte |
| dbt Core | dbt Cloud |
| MinIO | Amazon S3 / GCS / Azure Blob |
| Trino | Amazon Athena / BigQuery |
| Airflow | Amazon MWAA / Cloud Composer (GCP) |
| Keycloak | Amazon Cognito / Auth0 |
| Prometheus + Grafana | CloudWatch / Datadog |
| Superset | Looker / Tableau |
| Elementary | Monte Carlo / Great Expectations Cloud |
| Evidence | Observable / Hex |
| OpenMetadata | Google Dataplex / Microsoft Purview |

## WSL2 (Windows)

The platform runs on WSL2 (Ubuntu 22.04+). Set Docker Desktop -> Settings -> Resources -> "Use WSL 2 based engine". See [docs/wsl2.md](docs/wsl2.md) for full setup and known limitations.

## Sprint Status

| Story | Title | Status |
|---|---|---|
| **Epic 1** | **Project Foundation** | **in-progress** |
| 1.1 | Repository scaffold and dbt project initialisation | ✅ done |
| 1.2 | Makefile profile switching and service lifecycle | ✅ done |
| 1.3 | Port allocation and Docker Compose structure | ✅ done |
| **Epic 2** | **Simple Profile — First Working Pipeline (MVP)** | **in-progress** |
| 2.1 | Faker synthetic data generator | ✅ done |
| 2.2 | dlt file source ingestion to bronze | ✅ done |
| 2.3 | dlt API source ingestion to bronze | ✅ done |
| 2.4 | Silver layer dbt models with medallion structure | ✅ done |
| 2.5 | Quarantine models for failed record capture | ✅ done |
| 2.6 | Gold layer facts, dimensions and marts | ✅ done |
| 2.7 | MetricFlow semantic layer | ✅ done |
| 2.8 | dbt tests, dbt-expectations and source freshness | ✅ done |
| 2.9 | Elementary observability dashboard | ✅ done |
| 2.10 | Lightdash BI dashboard | deferred → 3.4 |
| 2.11 | Evidence analytical reports | ✅ done |
| 2.12 | make run-pipeline and make open-docs commands | ✅ done |
| 2.12b | Silver incremental idempotency fix | ✅ done |
| 2.13 | dbt documentation and column lineage | done |
| 2.14 | Cron schedule and README | done |
| **Epic 3** | **Postgres Profile — Server Warehouse & Governance** | **backlog** |
| 3.1 | Postgres profile Docker Compose and dbt adapter | backlog |
| 3.2 | Three-role RBAC and PII column masking | backlog |
| 3.3 | dbt schema contracts on serving layer | backlog |
| 3.4 | Lightdash BI dashboard | backlog |
| **Epic 4** | **Lakehouse Profile — Open Table Format & Distributed Query** | **backlog** |
| 4.1 | Lakehouse profile — MinIO, Iceberg and Trino | backlog |
| 4.2 | NYC Taxi dataset and schema evolution | backlog |
| 4.3 | OpenMetadata data catalog and cross-system lineage | backlog |
| 4.4 | Iceberg/Delta Lake/Hudi reference documentation | backlog |
| **Epic 5** | **Full Profile — Enterprise Data Platform** | **backlog** |
| 5.1 | Airflow orchestration with pipeline DAG | backlog |
| 5.2 | Prometheus and Grafana observability | backlog |
| 5.3 | Keycloak SSO and service authentication | backlog |
| 5.4 | Superset BI with Redis and Celery | backlog |
| 5.5 | MCP Server AI agent interface via MetricFlow | backlog |
| 5.6 | Pipeline alerting declared as code | backlog |

## Port Allocation

All services use a high-base port range (18000+) with 10-unit increments to avoid conflicts with common local services.

| Service | Host Port | Profile(s) | Status |
|---|---|---|---|
| Lightdash (BI dashboard) | 18000 | all | Stub — DuckDB adapter pending upstream; full support in Story 3.4 (Postgres) |
| Evidence (analytical reports) | 18010 | all | Active |
| dbt docs | 18020 | all | Active |
| Elementary (observability) | 18030 | all | Active |
| Postgres (data warehouse) | 18040 | postgres, full | Stub — used from Story 2 onwards |
| MinIO console | 18050 | lakehouse, full | Stub — configured in Story 4.1 |
| MinIO API (S3-compatible) | 18060 | lakehouse, full | Stub — configured in Story 4.1 |
| Trino (query engine) | 18070 | lakehouse, full | Stub — configured in Story 4.1 |
| Airflow webserver | 18080 | full | Stub — configured in Story 5.1 |
| OpenMetadata (data catalog) | 18090 | full | Stub — configured in Story 4.3 |
| Prometheus (metrics) | 18100 | full | Stub — configured in Story 5.2 |
| Grafana (dashboards) | 18110 | full | Stub — configured in Story 5.2 |
| Keycloak (SSO) | 18120 | full | Stub — configured in Story 5.3 |
| Superset (BI/exploration) | 18130 | full | Stub — configured in Story 5.4 |
| MCP Server (AI agent) | 18140 | full | Stub — configured in Story 5.5 |

> **DuckDB (simple profile):** DuckDB is file-based — no port required. Connect directly to `dev.duckdb` at repo root. See [Connecting to DuckDB](#connecting-to-duckdb-simple-profile) below.

## Connecting to DuckDB (simple profile)

After running the pipeline (`make run-pipeline`), the DuckDB file at `dev.duckdb` contains all layers including the `gold` schema.

**DuckDB CLI:**
```bash
duckdb dev.duckdb
D> SELECT * FROM gold.orders LIMIT 10;
```

**DataGrip / TablePlus / DBeaver:**
1. Choose "DuckDB" as the driver
2. Set the file path to the absolute path of `dev.duckdb` in this repo
3. Connect — no host/port/password required
4. Query: `SELECT * FROM gold.orders LIMIT 10;`

> Note: `dev.duckdb` is created when dbt first runs. Until then the file may not exist or the `gold` schema may be empty.
