# Profile Guide

This guide summarises the hardware needs, included services, and startup commands for each compose profile.

## `simple`

- Hardware: 8 GB RAM minimum
- Services: Lightdash, Evidence, dbt docs, Elementary, cron-scheduler
- Query engine: DuckDB file at `dev.duckdb`
- Start with: `cp .env.example .env` then `make start`

## `postgres`

- Hardware: 8 GB RAM minimum
- Services: everything in `simple` plus Postgres
- Query engine: Postgres warehouse for dbt targets and role-based access patterns
- Start with: set `COMPOSE_PROFILES=postgres` in `.env`, then run `make start`

## `lakehouse`

- Hardware: 16 GB RAM recommended
- Services: scheduler, Trino, MinIO, and the shared learning services
- Query engine: Trino over object storage and table-format based datasets
- Start with: set `COMPOSE_PROFILES=lakehouse` in `.env`, then run `make start`

## `full`

- Hardware: 16 GB RAM recommended
- Services: all local platform components including Airflow, Keycloak, Prometheus, Grafana, Superset, and OpenMetadata
- Query engine: combined warehouse, lakehouse, orchestration, governance, and BI stack
- Start with: set `COMPOSE_PROFILES=full` in `.env`, then run `make start`
