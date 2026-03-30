---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
workflowComplete: true
completedAt: '2026-03-25'
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/architecture.md"
---

# local-data-platform - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for local-data-platform, decomposing the requirements from the PRD and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Environment & Profile Management**
FR1: Learner can start a complete profile environment with a single command
FR2: Learner can stop all profile services with a single command
FR3: Learner can switch between deployment profiles via configuration without modifying pipeline code
FR4: Learner can view all available commands and their descriptions via a help command
FR5: Learner can execute the complete pipeline (ingestion → transformation → testing) with a single command
FR6: Learner can open documentation and observability dashboards in a browser with a single command
FR7: The system executes pipeline runs on a defined schedule (cron-based in `simple` profile, workflow-scheduled in `full` profile)

**Data Ingestion**
FR8: The system ingests data from file sources into the Bronze layer
FR9: The system ingests data from a REST API source into the Bronze layer
FR10: Learner can generate synthetic e-commerce data at configurable volume for use as pipeline input
FR11: The system appends raw data to the Bronze layer without modification or deletion — the Bronze layer is immutable
FR12: The system records ingestion metadata (source, run ID, timestamp) on every raw record

**Data Transformation**
FR13: Learner can execute dbt models across Bronze, Silver, and Gold layers
FR14: Learner can execute individual dbt models or model subsets by selector, tag, or path
FR15: The system structures all data through a Medallion architecture (Bronze → Silver → Gold)
FR16: The system executes transformations idempotently — re-running produces identical output with no duplicates
FR17: The system captures failed records with sufficient context to diagnose and replay them

**Data Quality & Observability**
FR18: Learner can view dbt test results (pass/fail) per model after each pipeline run
FR19: The system monitors source data freshness against declared SLAs and surfaces breaches
FR20: Learner can view an observability dashboard showing test pass rates, anomalies, freshness status, and schema changes
FR21: The system tracks and displays row counts and storage sizes per Medallion layer per pipeline run
FR22: Learner can trace a failed test to the specific model and column in the DAG
FR23: The system detects and surfaces schema changes across pipeline runs

**Data Access & Serving**
FR24: Learner can explore data and metrics via a dbt-native BI interface
FR25: Learner can view code-driven, version-controlled analytical reports
FR26: Learner can explore data via a traditional drag-and-drop BI dashboard interface (full profile)
FR27: Learner can query data directly via SQL using a standard client connection
FR28: The system exposes metrics and dimensions via a semantic layer with consistent, unambiguous business definitions
FR29: Learner can view the full dbt transformation DAG showing model dependencies and column lineage
FR30: The system provides cross-system data lineage from source through ingestion, transformation, and serving (full profile)

**Access Control & Governance**
FR31: The system enforces role-based access control across three roles: `engineer_role`, `analyst_role`, and `pii_analyst_role`
FR32: The `analyst_role` receives PII columns masked by default; the `pii_analyst_role` receives unmasked access via explicit grant only
FR33: The system logs every access to unmasked PII data
FR34: Learner can declare column descriptions, data types, PII tags, ownership, and test definitions in a single configuration artifact
FR35: The system enforces schema contracts on serving layer models, rejecting downstream consumption if the contract is violated
FR36: The system provides a data catalog with cross-system lineage and PII column classification (full profile)
FR37: The system authenticates all human and service-to-service access — no unauthenticated queries reach the data layer
FR38: The full profile provides local enterprise SSO simulation via an identity provider, with documented mapping to cloud IdP equivalents

**AI Agent Access**
FR39: An AI agent can query business metrics and dimensions via the semantic layer using natural language
FR40: AI agent access is subject to the same role-based access controls as human analyst access
FR41: The semantic layer prevents AI agents from querying raw tables directly — all queries route through defined metrics and dimensions
FR42: Learner can connect an MCP-compatible AI client to the data product's MCP server using documented connection instructions

**Alerting**
FR43: The system notifies a declared recipient when pipeline execution fails, quality tests breach thresholds, or source freshness SLAs are missed
FR44: Alert configuration is declared alongside pipeline and data contracts — not wired to a specific tool's UI — so alerting survives tool changes

**Documentation & Discoverability**
FR45: Learner can generate and serve dbt documentation showing model descriptions, column lineage, and test coverage
FR46: The system provides a cloud equivalence mapping table documenting the production equivalent of each local component
FR47: The system provides an open table format comparison reference (Iceberg, Delta Lake, Hudi) covering write performance, streaming support, and ecosystem alignment
FR48: The README documents hardware requirements, quick-start instructions, profile descriptions, and WSL2 compatibility notes
FR49: The system documents port allocations for all services in both the README and compose configuration

### NonFunctional Requirements

**Performance**
NFR1: The `simple` profile reaches a running state within 5 minutes on minimum hardware, after initial Docker image pull
NFR2: A full pipeline run (ingestion → dbt run → dbt test) on Jaffle Shop completes within 2 minutes on the `simple` profile
NFR3: dbt docs generation and serve completes within 30 seconds for the default dataset
NFR4: Lightdash and Evidence dashboards respond to initial page load within 10 seconds of pipeline completion
NFR5: The Faker data generator produces up to 100,000 rows within 60 seconds on minimum hardware

**Security**
NFR6: No credentials, secrets, or API keys are committed to the repository — all sensitive configuration stored in `.env` files excluded by `.gitignore`
NFR7: The repository ships with a `.env.example` file containing placeholder values only, documenting all required environment variables
NFR8: PII columns in the Faker dataset are masked for `analyst_role` by default — unmasked access requires explicit grant and is logged
NFR9: Service-to-service authentication uses local credentials via `.env`; the README documents the equivalent IAM role pattern for cloud deployments

**Integration**
NFR10: All Docker Compose configuration uses Docker Compose v2 syntax (`docker compose`, not `docker-compose`)
NFR11: All Docker images provide `linux/arm64` variants — images without ARM64 support are explicitly documented as known exceptions
NFR12: Each profile's dbt adapter version is tested against the declared query engine version; tested combinations are documented
NFR13: The MCP server conforms to the MCP protocol specification version in use at implementation; the version is documented
NFR14: The serving layer exposes a standard SQL interface (JDBC/ODBC-compatible) enabling connection from any standard BI client without template modification

**Reliability**
NFR15: Every profile starts cleanly from a fresh Docker state (`docker compose down -v` + `make start`) without manual intervention
NFR16: The pipeline is fully idempotent — running `make run-pipeline` twice produces identical row counts and test results
NFR17: dbt tests pass on a clean run for all profiles using default sample data
NFR18: The `simple` profile functions correctly on 8GB RAM; the `full` profile is documented as requiring 16GB RAM

**Maintainability**
NFR19: Each deployment profile is independently startable — modifying one profile does not break others
NFR20: All profile-specific configuration is isolated to `.env` and `docker-compose.yml` — dbt models, ingestion scripts, and `schema.yml` are shared across profiles and contain no profile-specific logic
NFR21: The Makefile is self-documenting — `make help` lists and describes every available target without requiring the user to read the Makefile source

### Additional Requirements

Architecture requirements that affect epic and story creation:

- **No starter template:** Project is itself a starter template; scaffold is native tool composition via `dbt init` + hand-crafted Docker Compose, Makefile, and `.env.example`. Epic 1 Story 1 must be project initialisation.
- **Initialisation sequence (Epic 1, Story 1):** `dbt init local_data_platform` → `dbt deps` → hand-craft `docker-compose.yml`, `Makefile`, `.env.example`
- **dbt at repo root:** `dbt_project.yml` lives at repo root (not a subdirectory) — affects all Makefile targets and Docker volume mounts
- **Schema naming:** Medallion layers as database schema names — `bronze`, `silver`, `gold`, `quarantine`
- **Bronze ownership boundary:** dlt owns and writes Bronze; dbt reads Bronze via `{{ source() }}` only — no `.sql` model files under `models/bronze/`. This must be structurally enforced.
- **Metadata column convention (Silver):** `_dlt_load_id` and `_dlt_id` inherited from Bronze; Silver models add `_loaded_at` (CURRENT_TIMESTAMP) and `_source` (literal string e.g. `'faker_orders_file'`)
- **Quarantine schema:** `quarantine` schema must be created in each engine's init script; every Silver model requires a corresponding `quarantine.{model}_failed` model capturing failed records with `_failed_reason` and `_failed_at`
- **Three-tier dbt portability:** Tier 1 (standard SQL in model files), Tier 2 (adapter dispatch macros in `macros/adapters/`), Tier 3 (engine-native RBAC/masking outside dbt). Stories must not mix tiers.
- **Incremental strategy:** `delete+insert` using `_dlt_id` as unique key — works across DuckDB, Postgres, Trino
- **Port allocation map:** 18000+ base, increments of 10. Documented per-service allocation must be applied consistently across `docker-compose.yml`, README, and `make help`.
- **schema.yml completeness rule:** Every model needs `description` + at least one test + all columns documented with `description`, `data_type`, `meta.pii: true/false`. Gold/mart models additionally require `constraints` block. A story is not complete if any model or column lacks this.
- **Maintainer CI:** Minimal GitHub Actions workflow (`dbt compile` + `sqlfluff` + `yamllint`) in `.github/workflows/ci.yml` — for maintainer use only, not learner-facing
- **dbt source declarations:** All Bronze tables declared in `models/bronze/sources.yml`; one `sources.yml` per source system
- **SQL style:** CTEs first (no inline subqueries), snake_case column names, UTC timestamps as `TIMESTAMP` type with `_at` suffix
- **Environment variable naming:** `SCREAMING_SNAKE_CASE` with service prefix (`POSTGRES_`, `MINIO_`, etc.)
- **Makefile targets:** `kebab-case` with `##` comment on every target for `make help` auto-documentation
- **ARM64 validation:** Required before including any service in any profile

### UX Design Requirements

No UX Design document found for this project. This is a developer tool — the primary interface is the Makefile CLI and dbt CLI, not a graphical UI.

### FR Coverage Map

FR1: Epic 1 — make start command
FR2: Epic 1 — make stop command
FR3: Epic 1 — profile switching via .env (validated in each subsequent epic)
FR4: Epic 1 — make help
FR5: Epic 2 — make run-pipeline
FR6: Epic 2 — make open-docs
FR7: Epic 2 (cron schedule) / Epic 5 (Airflow DAG)
FR8: Epic 2 — dlt file source → Bronze
FR9: Epic 2 — dlt API source → Bronze
FR10: Epic 2 — Faker synthetic data generator
FR11: Epic 2 — Bronze immutability
FR12: Epic 2 — ingestion metadata stamping
FR13: Epic 2 — dbt run all layers
FR14: Epic 2 — dbt run by selector/tag/path
FR15: Epic 2 — Medallion Bronze/Silver/Gold structure
FR16: Epic 2 — transformation idempotency
FR17: Epic 2 — quarantine failed records
FR18: Epic 2 — dbt test results per model
FR19: Epic 2 — source freshness monitoring
FR20: Epic 2 — Elementary observability dashboard
FR21: Epic 2 — row counts + storage by layer
FR22: Epic 2 — trace failed test to model in DAG
FR23: Epic 2 — schema change detection
FR24: Epic 2 — Lightdash (dbt-native BI)
FR25: Epic 2 — Evidence (code-driven reports)
FR26: Epic 5 — Superset drag-and-drop BI
FR27: Epic 2 — direct SQL client connection
FR28: Epic 2 — MetricFlow semantic layer
FR29: Epic 2 — dbt DAG + column lineage
FR30: Epic 4 — cross-system lineage (OpenMetadata)
FR31: Epic 3 — 3-role RBAC
FR32: Epic 3 — PII masking by role
FR33: Epic 3 — PII access logging
FR34: Epic 2 — schema.yml governance artifact (contracts enforced in Epic 3)
FR35: Epic 3 — dbt schema contracts on serving layer
FR36: Epic 4 — data catalog with PII classification (OpenMetadata)
FR37: Epic 5 — authenticated access (Keycloak SSO)
FR38: Epic 5 — local SSO simulation + cloud IdP mapping
FR39: Epic 5 — AI agent natural language queries via MCP
FR40: Epic 5 — AI agent subject to same RBAC as humans
FR41: Epic 5 — semantic layer prevents AI raw table access
FR42: Epic 5 — MCP connection documentation
FR43: Epic 5 — pipeline alerting
FR44: Epic 5 — alert config declared as code
FR45: Epic 2 — dbt docs generation + serve
FR46: Epic 2 — cloud equivalence table (docs/)
FR47: Epic 4 — Iceberg/Delta/Hudi comparison reference
FR48: Epic 2 — README (hardware, quick-start, WSL2 notes)
FR49: Epic 1 — port allocation documented

## Epic List

### Epic 1: Project Foundation
Learner can clone the repository and have a fully functional project scaffold — self-documenting Makefile, profile switching via `.env`, Docker Compose structure, and the dbt project skeleton — ready to receive pipeline code. The architecture is in place, all Makefile targets are documented, and profile isolation is proven.
**FRs covered:** FR1, FR2, FR3, FR4, FR49
**NFRs addressed:** NFR6, NFR7, NFR10, NFR15, NFR19, NFR20, NFR21

### Epic 2: Simple Profile — First Working Pipeline (MVP)
Learner runs `make start` on the `simple` profile (DuckDB) and within minutes has a working end-to-end pipeline: synthetic data generated and ingested via dlt into a Bronze/Silver/Gold Medallion structure, dbt models running and tested, Elementary observability dashboard accessible, Lightdash and Evidence available in the browser, and dbt docs browsable. This is the MVP — shareable with the community.
**FRs covered:** FR5, FR6, FR7 (cron), FR8–FR29, FR34, FR45, FR46, FR48
**NFRs addressed:** NFR1, NFR2, NFR3, NFR4, NFR5, NFR11, NFR12, NFR16, NFR17, NFR18

### Epic 3: Postgres Profile — Server Warehouse & Governance
**Prerequisite:** Epic 2 must be implemented first. The dbt models, `schema.yml`, and ingestion scripts from Epic 2 are shared infrastructure used unchanged by this profile.
Learner switches to the `postgres` profile and experiences a server-based warehouse with full three-role RBAC (`engineer_role`, `analyst_role`, `pii_analyst_role`), PII column masking enforced by default, dbt schema contracts on the serving layer, and direct SQL client connectivity. Governance patterns become tangible and testable.
**FRs covered:** FR31, FR32, FR33, FR34 (PII enforcement), FR35
**NFRs addressed:** NFR8, NFR9, NFR14

### Epic 4: Lakehouse Profile — Open Table Format & Distributed Query
**Prerequisite:** Epic 2 must be implemented first. The dbt models, `schema.yml`, and ingestion scripts from Epic 2 are shared infrastructure used unchanged by this profile.
Learner switches to the `lakehouse` profile and experiences query/storage separation: MinIO as object storage, Apache Iceberg as the table format, Trino as the query engine, and OpenMetadata providing cross-system data catalog and lineage. The NYC Taxi dataset introduces real, messy, multi-year data with schema evolution challenges. Includes the Iceberg/Delta Lake/Hudi reference comparison.
**FRs covered:** FR30, FR36, FR47
**NFRs addressed:** NFR11 (ARM64 lakehouse services), NFR12 (Trino adapter)

### Epic 5: Full Profile — Enterprise Data Platform
**Prerequisite:** Epics 2 and 3 must be implemented first. The dbt models from Epic 2 and the RBAC role definitions from Epic 3 are required. The `full` profile's Docker Compose init scripts must independently provision all three roles (`engineer_role`, `analyst_role`, `pii_analyst_role`) without relying on the Postgres profile's init scripts having been run.
Learner brings up the `full` profile and experiences the complete enterprise stack: Airflow orchestration with a pipeline DAG, Prometheus + Grafana observability, Keycloak SSO simulation, Superset BI, MCP Server exposing MetricFlow as an AI agent interface, and pipeline alerting declared as code alongside data contracts. The data product is queryable by both humans and AI agents with identical RBAC enforcement.
**FRs covered:** FR7 (Airflow DAG), FR26, FR37, FR38, FR39–FR44
**NFRs addressed:** NFR13

## Epic 1: Project Foundation

Learner can clone the repository and have a fully functional project scaffold — self-documenting Makefile, profile switching via `.env`, Docker Compose structure, and the dbt project skeleton — ready to receive pipeline code. The architecture is in place, all Makefile targets are documented, and profile isolation is proven.

### Story 1.1: Repository Scaffold and dbt Project Initialisation

As a data engineer,
I want a cloneable repository with a dbt project skeleton, Makefile, and `.env.example` already in place,
So that I can start from a working structure without manual setup steps.

**Acceptance Criteria:**

**Given** I have cloned the repository and have Docker Desktop running
**When** I run `make help`
**Then** all available Makefile targets are listed with descriptions, with no errors
**And** the output includes at minimum `start`, `stop`, `run-pipeline`, `open-docs`, and `help` targets

**Given** the repository is freshly cloned
**When** I inspect the root directory
**Then** `dbt_project.yml`, `profiles.yml`, `packages.yml`, `Makefile`, `.env.example`, `.gitignore`, and `docker-compose.yml` are all present at repo root
**And** `.env` is absent (excluded by `.gitignore`)

**Given** I copy `.env.example` to `.env`
**When** I inspect `.env.example`
**Then** all required environment variables are documented with placeholder values and inline comments
**And** no real credentials, secrets, or API keys are present

**Given** the dbt project skeleton exists
**When** I inspect the directory structure
**Then** `models/bronze/`, `models/silver/`, `models/gold/`, `models/quarantine/`, `models/metrics/`, `macros/`, `tests/`, `seeds/`, `analyses/`, `ingest/`, `data/`, `docker/`, `docs/`, `terraform/` are all present
**And** `models/bronze/` contains only `sources.yml` and `.gitkeep` — no `.sql` model files

---

### Story 1.2: Makefile Profile Switching and Service Lifecycle

As a data engineer,
I want to start and stop profile services using a single Makefile command and switch profiles via a single `.env` variable,
So that I can move between deployment profiles without modifying any pipeline code.

**Acceptance Criteria:**

**Given** `COMPOSE_PROFILES=simple` is set in `.env`
**When** I run `make start`
**Then** all `simple` profile services start successfully using Docker Compose v2 syntax
**And** no services from other profiles (`postgres`, `lakehouse`, `full`) are started

**Given** services are running
**When** I run `make stop`
**Then** all running services stop cleanly with exit code 0

**Given** I change `COMPOSE_PROFILES` in `.env` from `simple` to `postgres`
**When** I run `make start`
**Then** the `postgres` profile services start without any changes to dbt models, ingestion scripts, or `schema.yml`
**And** `make stop` cleanly stops the `postgres` profile services

**Given** a fresh Docker state (`docker compose down -v` completed)
**When** I run `make start` for any profile
**Then** services start cleanly without manual intervention

---

### Story 1.3: Port Allocation and Docker Compose Structure

As a data engineer,
I want all services assigned to documented, non-conflicting ports from a high base,
So that the template does not collide with other local services and I can find any service endpoint quickly.

**Acceptance Criteria:**

**Given** the `docker-compose.yml` is implemented
**When** I inspect all service port declarations
**Then** all ports use the 18000+ base with increments of 10, matching the port map: Lightdash=18000, Evidence=18010, dbt docs=18020, Elementary=18030, Postgres=18040, MinIO console=18050, MinIO API=18060, Trino=18070, Airflow=18080, OpenMetadata=18090, Prometheus=18100, Grafana=18110, Keycloak=18120, Superset=18130, MCP Server=18140
**And** no two services share the same host port

**Given** the README exists
**When** I search for the port allocation section
**Then** a complete port map table is present matching the `docker-compose.yml` declarations

**Given** I run `make help`
**When** I read the output
**Then** resource requirements per profile (RAM) are documented alongside the relevant targets

**Given** the `simple` profile is running
**When** I follow the connection string documented in the README
**Then** I can connect a standard SQL client (e.g. DuckDB CLI, DataGrip, or TablePlus) to the running DuckDB instance and query the `gold` schema directly — satisfying FR27

---

## Epic 2: Simple Profile — First Working Pipeline (MVP)

Learner runs `make start` on the `simple` profile (DuckDB) and within minutes has a working end-to-end pipeline: synthetic data generated and ingested via dlt into a Bronze/Silver/Gold Medallion structure, dbt models running and tested, Elementary observability dashboard accessible, Lightdash and Evidence available in the browser, and dbt docs browsable. This is the MVP — shareable with the community.

### Story 2.1: Faker Synthetic Data Generator

As a data engineer,
I want to generate configurable volumes of synthetic e-commerce data (orders, customers, products, returns),
So that I have realistic pipeline input without depending on external data sources.

**Acceptance Criteria:**

**Given** I have Python dependencies installed (`pip install -r ingest/requirements.txt`)
**When** I run the Faker generator with default settings
**Then** four CSV/JSON files are produced: orders, customers, products, returns — each with realistic column types and referential integrity between entities

**Given** I set a volume parameter (e.g. `FAKER_ROWS=10000`)
**When** I run the generator
**Then** the specified number of rows is produced per entity within 60 seconds on minimum hardware (8GB RAM)

**Given** the generator output
**When** I inspect the data
**Then** PII columns (customer name, email, address) are present and clearly identifiable in the schema
**And** at least one column per entity is tagged `meta.pii: true` in `schema.yml`

**Given** the repository is freshly cloned and `make start` has been run on the `simple` profile
**When** I run `make run-pipeline`
**Then** Jaffle Shop seed data is automatically available as a pipeline source without any manual setup
**And** dbt tests pass against the Jaffle Shop dataset completing within 2 minutes (NFR2)

---

### Story 2.2: dlt File Source Ingestion to Bronze

As a data engineer,
I want dlt to ingest data from local file drops into the Bronze layer with full metadata stamping,
So that raw data lands immutably with auditable provenance before any transformation occurs.

**Acceptance Criteria:**

**Given** sample files exist in `data/`
**When** I run the dlt file source pipeline (`dlt_file_source.py`)
**Then** raw records land in the `bronze` schema in DuckDB with zero modification to source values

**Given** Bronze tables are populated
**When** I inspect the table schema
**Then** `_dlt_load_id` and `_dlt_id` columns are present on every Bronze table (dlt native columns, not renamed)
**And** no other metadata columns are added at the Bronze layer

**Given** I run the file source pipeline twice on the same source files
**When** I count Bronze rows
**Then** row count does not increase — dlt deduplicates using `_dlt_id`

**Given** a pipeline run completes
**When** I inspect the Bronze schema in DuckDB
**Then** no dbt materializations exist in `bronze` — the schema contains only dlt-written tables

---

### Story 2.3: dlt API Source Ingestion to Bronze

As a data engineer,
I want dlt to ingest data from a REST API source into the Bronze layer,
So that I experience both file-based and API-based ingestion patterns in a single pipeline.

**Acceptance Criteria:**

**Given** the dlt API source script is configured with endpoint details in `.env`
**When** I run `dlt_api_source.py`
**Then** records from the API response land in the `bronze` schema with `_dlt_load_id` and `_dlt_id` stamped

**Given** the pipeline errors (e.g. endpoint unreachable)
**When** the exception occurs
**Then** the error is logged to stdout in structured JSON format `{"level": "ERROR", "pipeline": "...", "error": "..."}`
**And** the script exits with code 1 (detectable by Makefile and cron)

---

### Story 2.4: Silver Layer dbt Models with Medallion Structure

As a data engineer,
I want dbt Silver models that read from Bronze, clean and deduplicate records, and add transformation metadata,
So that a clean, consistent representation of each entity is available for Gold layer consumption.

**Acceptance Criteria:**

**Given** Bronze tables are populated
**When** I run `dbt run --select tag:silver`
**Then** four Silver models materialise: `silver.faker_orders`, `silver.faker_customers`, `silver.faker_products`, `silver.faker_returns`

**Given** a Silver model runs
**When** I inspect the resulting table schema
**Then** `_dlt_load_id`, `_dlt_id`, `_loaded_at` (CURRENT_TIMESTAMP), and `_source` (string literal) are present on every Silver table
**And** all column names are `snake_case`
**And** all timestamp columns use `TIMESTAMP` type (not VARCHAR or epoch)

**Given** I run `dbt run --select tag:silver` twice on the same Bronze data
**When** I count Silver rows after each run
**Then** row counts are identical — incremental `delete+insert` strategy using `_dlt_id` as unique key

**Given** a Silver model file
**When** I inspect the SQL
**Then** the model uses CTEs exclusively (no inline subqueries)
**And** `{{ source('faker', 'table') }}` is used — no hardcoded `bronze.table` references

**Given** the Silver `schema.yml`
**When** I inspect it
**Then** every model has a `description`, at least one test, and every column has `description`, `data_type`, and `meta.pii: true/false`

---

### Story 2.5: Quarantine Models for Failed Record Capture

As a data engineer,
I want failed records from Silver models to land in a dedicated quarantine schema with failure context,
So that pipeline failures are visible and diagnosable without hunting through logs.

**Acceptance Criteria:**

**Given** a Silver model encounters records that fail validation rules
**When** the dbt pipeline runs
**Then** rejected records land in `quarantine.faker_orders_failed` (and equivalent tables for each Silver model)
**And** each quarantine record includes the original row data plus `_failed_reason` (string) and `_failed_at` (timestamp)

**Given** the DuckDB init script runs on `make start`
**When** I inspect the DuckDB schemas
**Then** the `quarantine` schema exists before any dbt run

**Given** I run `make run-pipeline` twice on clean data
**When** I query `quarantine.*`
**Then** quarantine tables exist but contain zero rows (idempotent clean run)

---

### Story 2.6: Gold Layer — Facts, Dimensions, and Marts

As a data engineer,
I want dbt Gold models (facts, dimensions, marts) that serve clean, business-ready data for BI and the semantic layer,
So that downstream consumers (Lightdash, Evidence, MetricFlow) have a stable, governed serving layer.

**Acceptance Criteria:**

**Given** Silver models are populated
**When** I run `dbt run --select tag:gold`
**Then** `gold.fct_orders`, `gold.dim_customers`, `gold.dim_products`, and `gold.orders_mart` materialise successfully

**Given** Gold mart models
**When** I inspect their `schema.yml`
**Then** every Gold model has a `constraints` block defining the dbt contract
**And** every column has `description`, `data_type`, and `meta.pii: true/false`

**Given** I run `dbt run --select tag:gold` twice
**When** I count rows
**Then** row counts are identical (idempotent)

---

### Story 2.7: MetricFlow Semantic Layer

As a data engineer,
I want MetricFlow metric definitions that expose business metrics and dimensions via a semantic layer,
So that BI tools and AI agents query consistent, unambiguous metric definitions rather than raw tables.

**Acceptance Criteria:**

**Given** MetricFlow metric definitions exist in `models/metrics/`
**When** I run `dbt sl list metrics`
**Then** at least two metrics are listed (e.g. `order_count`, `revenue`) with associated dimensions

**Given** a metric definition
**When** I query it via `dbt sl query --metrics order_count --group-by metric_time`
**Then** results are returned and match the expected values from the Gold layer

**Given** a query for an undefined metric or raw table reference
**When** MetricFlow processes the request
**Then** the query is rejected — no hallucinated joins to Bronze or Silver tables

---

### Story 2.8: dbt Tests, dbt-expectations, and Source Freshness

As a data engineer,
I want comprehensive dbt tests (generic, dbt-expectations, and source freshness checks) running after every pipeline execution,
So that data quality issues surface as visible failures rather than silent data corruption.

**Acceptance Criteria:**

**Given** dbt tests are declared in `schema.yml` for all Silver and Gold models
**When** I run `dbt test`
**Then** all tests pass on a clean run with default sample data

**Given** I intentionally introduce a type mismatch in a Silver model
**When** I run `dbt test`
**Then** the relevant test fails and the error message identifies the model and column

**Given** source freshness thresholds are declared in `models/bronze/sources.yml`
**When** I run `dbt source freshness`
**Then** freshness status (pass/warn/error) is reported per source

**Given** dbt-expectations is installed via `packages.yml`
**When** I run `dbt deps && dbt test`
**Then** dbt-expectations tests run alongside generic tests without errors

---

### Story 2.9: Elementary Observability Dashboard

As a data engineer,
I want an Elementary dashboard showing test pass rates, anomaly detection, source freshness status, and schema changes,
So that data quality is visible as a live observability layer — not just a pass/fail exit code.

**Acceptance Criteria:**

**Given** `make start` has been run and dbt tests have executed
**When** I open `http://localhost:18030`
**Then** the Elementary dashboard loads within 10 seconds and displays test results from the most recent pipeline run

**Given** the Elementary dashboard is open
**When** I navigate to the test results view
**Then** pass/fail rates are shown per model, I can drill into individual test failures, and source freshness status is visible

**Given** a schema change occurs between pipeline runs (e.g. a column is renamed in the source)
**When** I view the Elementary dashboard after the next run
**Then** the schema change is surfaced as a detectable event

**Given** `make run-pipeline` has completed
**When** I view the Elementary dashboard or the pipeline run summary output
**Then** row counts per Medallion layer (Bronze, Silver, Gold) are visible and storage sizes per layer are reported or logged — satisfying FR21

---

### Story 2.10: Lightdash BI Dashboard

As a data engineer,
I want Lightdash running against the Gold layer with pre-built explores,
So that I can browse metrics and dimensions via a dbt-native BI interface without additional configuration.

**Acceptance Criteria:**

**Given** `make start` has been run and `make run-pipeline` has completed
**When** I open `http://localhost:18000`
**Then** Lightdash loads within 10 seconds and at least one explore is available based on Gold models

**Given** I navigate to an explore in Lightdash
**When** I add a metric and dimension to a chart
**Then** results are returned and the underlying SQL references the Gold layer

---

### Story 2.11: Evidence Analytical Reports

As a data engineer,
I want Evidence reports committed to the repository as code,
So that I can see version-controlled, reproducible analytical outputs alongside the pipeline code.

**Acceptance Criteria:**

**Given** `make start` has been run and pipeline has executed
**When** I open `http://localhost:18010`
**Then** the Evidence app loads and displays at least one report showing pipeline output data

**Given** the Evidence report files in the repository
**When** I inspect them
**Then** they are SQL + Markdown files committed to source control — not generated artifacts

---

### Story 2.12: make run-pipeline and make open-docs Commands

As a data engineer,
I want `make run-pipeline` to execute the full pipeline in one command and `make open-docs` to open all dashboards,
So that the learner UX requires no knowledge of underlying tool commands for standard workflows.

**Acceptance Criteria:**

**Given** services are running
**When** I run `make run-pipeline`
**Then** ingestion → `dbt run` → `dbt test` executes in sequence and the command exits 0 on success, 1 on failure

**Given** `make run-pipeline` completes successfully
**When** I run `make open-docs`
**Then** dbt docs (18020), Elementary dashboard (18030), Lightdash (18000), and Evidence (18010) all open in the browser

**Given** I run `make run-pipeline` twice on the same data
**When** I compare row counts and dbt test results after each run
**Then** they are identical — pipeline is fully idempotent

---

### Story 2.13: dbt Documentation and Column Lineage

As a data engineer,
I want dbt docs generated and served showing model descriptions, column lineage, and test coverage,
So that I can navigate the full transformation DAG and understand how data moves through the pipeline.

**Acceptance Criteria:**

**Given** `make run-pipeline` has completed
**When** I run `dbt docs generate && dbt docs serve` (or via `make open-docs`)
**Then** dbt docs are available at `http://localhost:18020` within 30 seconds

**Given** dbt docs are open
**When** I navigate to a Gold model
**Then** column lineage traces back through Silver to Bronze source tables
**And** every model and column has a description (no undocumented nodes)

---

### Story 2.14: Cron Schedule and README

As a data engineer,
I want the `simple` profile to run the pipeline on a cron schedule and the README to provide everything needed for a first-time learner to get started,
So that the pipeline runs automatically after `make start` and a new learner can be productive within 10 minutes of cloning.

**Acceptance Criteria:**

**Given** `make start` has been run on the `simple` profile
**When** the scheduled interval elapses
**Then** the pipeline executes automatically without manual `make run-pipeline` invocation

**Given** a new learner clones the repository
**When** they read the README
**Then** it contains: hardware requirements (8GB min / 16GB recommended), quick-start instructions (clone → copy .env → make start), profile descriptions, cloud equivalence table, and WSL2 compatibility notes

**Given** the README cloud equivalence table
**When** I inspect it
**Then** every local component (DuckDB, MinIO, Trino, Airflow, Keycloak, Prometheus/Grafana, Superset) maps to its cloud equivalent

---

## Epic 3: Postgres Profile — Server Warehouse & Governance

**Prerequisite:** Epic 2 must be implemented first. The dbt models, `schema.yml`, and ingestion scripts from Epic 2 are shared infrastructure used unchanged by this profile.

Learner switches to the `postgres` profile and experiences a server-based warehouse with full three-role RBAC, PII column masking enforced by default, dbt schema contracts on the serving layer, and direct SQL client connectivity.

### Story 3.1: Postgres Profile Docker Compose and dbt Adapter

As a data engineer,
I want the `postgres` profile to start a Postgres container with the dbt-postgres adapter configured via `.env`,
So that I can switch to a server warehouse with zero changes to dbt models.

**Acceptance Criteria:**

**Given** `COMPOSE_PROFILES=postgres` is set in `.env`
**When** I run `make start`
**Then** a Postgres container starts on port 18040 and the `bronze`, `silver`, `gold`, `quarantine` schemas are created by the init script

**Given** the Postgres profile is running
**When** I run `make run-pipeline`
**Then** the same dbt models that ran on DuckDB execute without modification on Postgres
**And** dbt test results are identical to the `simple` profile on equivalent data

**Given** the Postgres init script runs
**When** I inspect the database schemas
**Then** `engineer_role`, `analyst_role`, and `pii_analyst_role` roles exist with appropriate schema-level grants

---

### Story 3.2: Three-Role RBAC and PII Column Masking

As a data engineer,
I want three database roles enforced at the engine level with PII columns masked for `analyst_role` by default,
So that I can experience and teach access control patterns that transfer directly to production data platforms.

**Acceptance Criteria:**

**Given** the Postgres profile is running with RBAC configured
**When** I connect as `analyst_role` and query a Gold model containing PII columns
**Then** PII columns (tagged `meta.pii: true` in `schema.yml`) return masked values (e.g. hashed or nulled)

**Given** `pii_analyst_role` has been explicitly granted unmasked access
**When** I connect as `pii_analyst_role` and query the same Gold model
**Then** PII columns return unmasked values

**Given** unmasked PII data is accessed
**When** I inspect the Postgres access log
**Then** the access event is recorded with role, timestamp, and table/column accessed

**Given** `engineer_role`
**When** I connect as `engineer_role`
**Then** I have full read/write access to all schemas including `bronze`

---

### Story 3.3: dbt Schema Contracts on Serving Layer

As a data engineer,
I want dbt schema contracts enforced on all Gold/mart models,
So that downstream consumers (BI tools, the semantic layer) fail fast and explicitly if the serving layer schema changes unexpectedly.

**Acceptance Criteria:**

**Given** Gold models have `constraints` blocks in `schema.yml`
**When** I run `dbt run --select tag:gold`
**Then** dbt enforces the contract and the run succeeds with no contract violations on clean data

**Given** I modify a Gold model to remove a contracted column
**When** I run `dbt run --select tag:gold`
**Then** the run fails with a clear contract violation error identifying the missing column

---

## Epic 4: Lakehouse Profile — Open Table Format & Distributed Query

**Prerequisite:** Epic 2 must be implemented first. The dbt models, `schema.yml`, and ingestion scripts from Epic 2 are shared infrastructure used unchanged by this profile.

Learner switches to the `lakehouse` profile and experiences query/storage separation, open table format, cross-system data catalog, and real-world messy data.

### Story 4.1: Lakehouse Profile — MinIO, Iceberg, and Trino

As a data engineer,
I want the `lakehouse` profile to start MinIO, Trino, and an Iceberg catalog, with dbt-trino configured via `.env`,
So that I can experience query/storage separation and open table format patterns locally.

**Acceptance Criteria:**

**Given** `COMPOSE_PROFILES=lakehouse` is set in `.env`
**When** I run `make start`
**Then** MinIO (console: 18050, API: 18060), Trino (18070), and an Iceberg metastore start without errors
**And** `bronze`, `silver`, `gold`, `quarantine` schemas are created in Trino

**Given** the lakehouse profile is running
**When** I run `make run-pipeline`
**Then** the same Tier 1 dbt models (standard SQL) execute on Trino without modification
**And** Iceberg-specific features (time travel, partition transforms) are demonstrated in `analyses/` — not in production model files

---

### Story 4.2: NYC Taxi Dataset and Schema Evolution

As a data engineer,
I want the NYC Taxi dataset loaded via dlt as an advanced data track,
So that I experience real, messy, multi-year data with schema evolution challenges.

**Acceptance Criteria:**

**Given** the lakehouse profile is running
**When** I run the NYC Taxi dlt ingestion script
**Then** TLC trip records land in the `bronze` schema with `_dlt_load_id` and `_dlt_id` stamped

**Given** data from multiple NYC Taxi years is ingested
**When** I run Silver models
**Then** schema evolution handling (new/removed columns across years) is demonstrated and documented

---

### Story 4.3: OpenMetadata Data Catalog and Cross-System Lineage

As a data engineer,
I want OpenMetadata running with cross-system lineage from source through ingestion, transformation, and serving,
So that I can see full end-to-end data lineage in a production-equivalent catalog.

**Acceptance Criteria:**

**Given** the lakehouse profile is running with OpenMetadata
**When** I open the OpenMetadata UI
**Then** Bronze, Silver, and Gold tables are catalogued with column-level lineage visible

**Given** OpenMetadata has ingested pipeline metadata
**When** I search for a Gold table
**Then** I can trace its lineage back to the Bronze source table through the Silver transformation

**Given** the data catalog
**When** I view a table with PII-tagged columns
**Then** PII classification is reflected in the catalog based on `schema.yml` `meta.pii` tags

---

### Story 4.4: Iceberg/Delta Lake/Hudi Reference Documentation

As a data engineer,
I want a reference document comparing Iceberg, Delta Lake, and Hudi across key dimensions,
So that I understand why Iceberg was chosen as the default and can evaluate alternatives in context.

**Acceptance Criteria:**

**Given** `docs/open-table-formats.md` exists
**When** I read it
**Then** it covers: write performance, streaming/upsert support, ecosystem alignment (Spark, Trino, cloud warehouse compatibility), and a clear rationale for the Iceberg default

---

## Epic 5: Full Profile — Enterprise Data Platform

**Prerequisite:** Epics 2 and 3 must be implemented first. The `full` profile's Docker Compose init scripts must independently provision all three RBAC roles (`engineer_role`, `analyst_role`, `pii_analyst_role`) — do not rely on the Postgres profile's init scripts having been run.

Learner brings up the `full` profile and experiences Airflow orchestration, Prometheus/Grafana monitoring, Keycloak SSO, Superset BI, MCP Server as AI interface, and alerting declared as code.

### Story 5.1: Airflow Orchestration with Pipeline DAG

As a data engineer,
I want an Airflow DAG that orchestrates the full pipeline (ingestion → dbt run → dbt test) with dependency tracking,
So that I can experience workflow-based scheduling as an alternative to cron.

**Acceptance Criteria:**

**Given** `COMPOSE_PROFILES=full` is set and `make start` has been run
**When** I open the Airflow UI at `http://localhost:18080`
**Then** the pipeline DAG is visible and shows ingestion → dbt run → dbt test as dependent tasks

**Given** the Airflow DAG is triggered
**When** the run completes
**Then** each task shows pass/fail status and logs are accessible per task

**Given** a dbt test failure occurs during the DAG run
**When** the DAG task for dbt test executes
**Then** the task fails and the DAG marks the run as failed — it does not proceed to downstream tasks

**Given** the `full` profile starts from a fresh state (no prior Postgres profile having been run)
**When** the Docker Compose init scripts complete
**Then** `engineer_role`, `analyst_role`, and `pii_analyst_role` database roles exist and are correctly granted — the full profile is self-contained and does not depend on Epic 3's Postgres init scripts

---

### Story 5.2: Prometheus and Grafana Observability

As a data engineer,
I want Prometheus scraping pipeline metrics and Grafana displaying them on a pre-built dashboard,
So that I can experience infrastructure-level observability alongside dbt's data-level observability.

**Acceptance Criteria:**

**Given** the full profile is running
**When** I open Grafana at `http://localhost:18110`
**Then** a pre-built dashboard shows pipeline run metrics: run count, last run duration, test pass rate, and failure count

**Given** a pipeline run completes
**When** I view the Grafana dashboard
**Then** the latest run's metrics are reflected within the dashboard refresh interval

---

### Story 5.3: Keycloak SSO and Service Authentication

As a data engineer,
I want Keycloak providing SSO simulation for the full profile with documented mapping to cloud IdP equivalents,
So that I experience enterprise authentication patterns locally.

**Acceptance Criteria:**

**Given** the full profile is running
**When** I open Keycloak at `http://localhost:18120`
**Then** the Keycloak admin console is accessible and the `data-platform` realm is pre-configured

**Given** Keycloak is configured
**When** I access a protected service (e.g. Superset) via the SSO flow
**Then** authentication routes through Keycloak before granting access

**Given** `docs/rbac-guide.md` exists
**When** I read it
**Then** the three-role RBAC is explained per engine (DuckDB, Postgres, Trino) with mapping to cloud IdP equivalents (Okta, Azure AD, Google Workspace)

---

### Story 5.4: Superset BI with Redis and Celery

As a data engineer,
I want Apache Superset running against the Gold layer with its Redis and Celery workers bootstrapped via an init container,
So that I can experience a traditional drag-and-drop BI tool alongside the code-driven Evidence and dbt-native Lightdash.

**Acceptance Criteria:**

**Given** the full profile starts
**When** Superset init container runs
**Then** Superset database is initialised, admin user is created, and Superset is accessible at `http://localhost:18130`

**Given** Superset is running
**When** I connect it to the Gold layer and create a simple chart
**Then** the chart queries the Gold layer and returns results

---

### Story 5.5: MCP Server — AI Agent Interface via MetricFlow

As a data engineer,
I want an MCP server wrapping MetricFlow that allows an AI agent to query business metrics using natural language,
So that I can experience and demonstrate AI-native data product access with the same RBAC as human analysts.

**Acceptance Criteria:**

**Given** the full profile is running
**When** I follow `docs/mcp-connection.md` to connect an MCP-compatible client
**Then** the client connects to the MCP server at `http://localhost:18140` successfully

**Given** an AI agent connected via MCP queries `"What was total revenue last month?"`
**When** MetricFlow processes the query
**Then** the result is returned based on the `revenue` metric definition — no raw Bronze or Silver tables are queried

**Given** the AI agent connects with `analyst_role` credentials
**When** it attempts to query a metric that involves PII columns
**Then** PII data is masked — identical behaviour to a human `analyst_role` connection

**Given** the AI agent queries a metric not defined in MetricFlow
**When** the query is processed
**Then** it is rejected with a clear error — no hallucinated joins or raw table access occurs

**Given** `docs/mcp-connection.md` exists
**When** I read it
**Then** it documents the MCP protocol version implemented and step-by-step connection instructions for an MCP-compatible client

---

### Story 5.6: Pipeline Alerting Declared as Code

As a data engineer,
I want pipeline failure, quality test breach, and freshness SLA miss alerts declared in configuration alongside pipeline code,
So that alerting is a first-class, tool-agnostic contract — not wired to any specific tool's UI.

**Acceptance Criteria:**

**Given** alert configuration is declared in a YAML/config file alongside dbt and pipeline code
**When** a pipeline execution fails
**Then** the declared recipient receives a notification via the configured channel

**Given** a dbt quality test breaches its threshold
**When** the test runs
**Then** an alert is triggered matching the declaration in the alert config

**Given** a source freshness SLA is missed
**When** freshness is checked
**Then** an alert fires without requiring manual configuration in any tool UI

**Given** the alert config file
**When** I inspect it
**Then** all alert conditions (pipeline failure, quality breach, freshness miss) are declared as code — removing a tool does not silently disable alerting
