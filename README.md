# local-data-platform

A self-contained, profile-switchable local data platform for learning modern data engineering patterns — dbt, dlt, DuckDB, Postgres, Iceberg/Trino, and more.

## Quick Start

<!-- Full quick-start instructions added in Story 2.14 -->

## Hardware Requirements

- **Minimum (simple / postgres profiles):** 8 GB RAM
- **Recommended (lakehouse / full profiles):** 16 GB RAM

## Sprint Status

| Story | Title | Status |
|---|---|---|
| **Epic 1** | **Project Foundation** | **in-progress** |
| 1.1 | Repository scaffold and dbt project initialisation | ✅ done |
| 1.2 | Makefile profile switching and service lifecycle | ✅ done |
| 1.3 | Port allocation and Docker Compose structure | ✅ done |
| **Epic 2** | **Simple Profile — First Working Pipeline (MVP)** | **in-progress** |
| 2.1 | Faker synthetic data generator | review |
| 2.2 | dlt file source ingestion to bronze | backlog |
| 2.3 | dlt API source ingestion to bronze | backlog |
| 2.4 | Silver layer dbt models with medallion structure | backlog |
| 2.5 | Quarantine models for failed record capture | backlog |
| 2.6 | Gold layer facts, dimensions and marts | backlog |
| 2.7 | MetricFlow semantic layer | backlog |
| 2.8 | dbt tests, dbt-expectations and source freshness | backlog |
| 2.9 | Elementary observability dashboard | backlog |
| 2.10 | Lightdash BI dashboard | backlog |
| 2.11 | Evidence analytical reports | backlog |
| 2.12 | make run-pipeline and make open-docs commands | backlog |
| 2.13 | dbt documentation and column lineage | backlog |
| 2.14 | Cron schedule and README | backlog |
| **Epic 3** | **Postgres Profile — Server Warehouse & Governance** | **backlog** |
| 3.1 | Postgres profile Docker Compose and dbt adapter | backlog |
| 3.2 | Three-role RBAC and PII column masking | backlog |
| 3.3 | dbt schema contracts on serving layer | backlog |
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
| Lightdash (BI dashboard) | 18000 | all | Active |
| Evidence (analytical reports) | 18010 | all | Stub — configured in Story 2.11 |
| dbt docs | 18020 | all | Stub — configured in Story 2.13 |
| Elementary (observability) | 18030 | all | Stub — configured in Story 2.9 |
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
