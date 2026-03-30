---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-03-25'
inputDocuments:
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/brainstorming/brainstorming-session-2026-03-24-1200.md"
workflowType: 'architecture'
project_name: 'local-data-platform'
user_name: 'Iain'
date: '2026-03-25'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:** 49 FRs across 9 categories

| Category | Count | Key Architectural Driver |
|---|---|---|
| Environment & Profile Management | 7 | 5 independently-startable profiles; single-command UX |
| Data Ingestion | 5 | Immutable Bronze layer; metadata stamping; idempotent loading |
| Data Transformation | 5 | Shared dbt project across engines; Medallion layers; idempotency |
| Data Quality & Observability | 6 | Elementary on all profiles; layer-level metrics; schema change detection |
| Data Access & Serving | 7 | Semantic layer as canonical interface; cross-system lineage |
| Access Control & Governance | 8 | 3-role RBAC across heterogeneous query engines; PII masking |
| AI Agent Access | 4 | MCP Server wrapping MetricFlow; RBAC parity with human consumers |
| Alerting | 2 | Alert config as pipeline contract; tool-agnostic declaration |
| Documentation & Discoverability | 5 | schema.yml as governance + AI context artifact |

**Non-Functional Requirements:** 21 NFRs across 5 categories

| Category | Count | Key Architectural Driver |
|---|---|---|
| Performance | 5 | `simple` profile running in <5 min; pipeline in <2 min |
| Security | 4 | No credentials in repo; PII masking by default; IAM-documented |
| Integration | 5 | ARM64-first; Docker Compose v2; MCP protocol version-locked |
| Reliability | 4 | Clean cold-start; full idempotency; profile isolation |
| Maintainability | 3 | Profile config isolated to `.env`/compose; Makefile self-documenting |

**Scale & Complexity:**

- Primary domain: Data infrastructure / Developer tooling (greenfield)
- Complexity level: Medium-High — multi-engine abstraction, RBAC across heterogeneous compute, AI interface layer, 5 deployment profiles
- Estimated architectural components: ~20 discrete services across profiles; ~8 architectural layers

### Technical Constraints & Dependencies

- **ARM64-first:** All Docker images must provide `linux/arm64` — hard gate on service inclusion
- **`.env` + `profiles.yml` as the portability layer:** All profile differences must flow through these; dbt models contain zero profile-specific logic
- **Docker Compose v2 syntax** (`docker compose`, not `docker-compose`)
- **Resource floors:** 8GB RAM for `simple`/`postgres`; 16GB for `lakehouse`/`full`
- **Port allocation:** High base (18000+), increments of 10, fully documented
- **`latest` image tags:** Intentional for learning context; documented as anti-pattern for production
- **MCP protocol version:** Must be pinned and documented at implementation time

**dbt Portability Constraint (Three-Tier Model):**

A deliberate architectural constraint: a single dbt project runs across all deployment profiles. This is feasible and pedagogically intentional — it demonstrates dbt's adapter abstraction and Invariant 6 (governance survives a tool swap). However the constraint has known fracture points that must be documented explicitly rather than papered over:

| Tier | Scope | Constraint |
|---|---|---|
| **Tier 1 — Portable SQL** | All Bronze/Silver/Gold dbt models | Single project, standard SQL — runs unchanged across DuckDB, Postgres, and Trino |
| **Tier 2 — Adapter macros** | Incremental strategies, engine hints | `dbt dispatch` used where adapter behaviour diverges (e.g. merge vs insert_overwrite) |
| **Tier 3 — Engine-native** | RBAC, PII masking, Iceberg features | Implemented per-engine outside dbt models; schema.yml declares policy, engine enforces it |

Tier 3 is the most important fracture point. PII column masking cannot be implemented the same way across engines — Postgres has row-level security and column-level masking, Trino has access control plugins, DuckDB has minimal native support. The `pii: true` tag in schema.yml is the *portable declaration*; enforcement is engine-specific configuration. This separation is Invariant 4 in practice: "enforce at the data, not the interface."

Iceberg-specific features (time travel, partition transforms, metadata queries) are similarly Tier 3 — Trino/Spark profile only, and any learning exercises for those features cannot share the same model with DuckDB/Postgres profiles.

Documentation must make this three-tier distinction explicit: *"These models run on every profile because they use standard SQL — deliberately. In a production environment with a single engine, you would use engine-native features to get the most from your chosen stack. The portability here is the lesson, not the recommendation."*

### Cross-Cutting Concerns Identified

1. **Idempotency** — affects ingestion (merge/upsert, not insert), transformation (deterministic keys, run-ID stamping), and testing. Must be enforced at design level, not convention.
2. **ARM64 compatibility** — every service added to any profile requires ARM64 validation before inclusion
3. **PII column masking** — Tier 3 concern: declared in schema.yml, enforced differently per engine (Postgres RLS, Trino access control, DuckDB limited). RBAC must be consistent at the semantic layer regardless of underlying engine.
4. **`.env`-driven configuration isolation** — the mechanism that makes profiles switchable; all service configs must read from env vars, no hardcoded values
5. **schema.yml as dual artifact** — simultaneously the governance document and the AI interface specification; completeness directly determines AI agent answer quality
6. **Semantic layer as mandatory AI/BI interface** — MetricFlow is the access boundary; architecture must prevent bypass paths to raw tables
7. **Makefile as learner UX contract** — `make help` must remain self-documenting; all learner-facing operations must be exposed as named targets
8. **dbt three-tier portability boundary** — the line between Tier 1 (portable models), Tier 2 (adapter macros), and Tier 3 (engine-native) must be consciously maintained and documented; drift into Tier 3 inside dbt models breaks the cross-profile constraint

## Starter Template Evaluation

### Primary Technology Domain

Docker Compose-based data infrastructure / developer tooling template. No single CLI scaffold exists for this stack — the project is itself a starter template, composed from native tool scaffolds.

### Reference Templates Considered

| Template | Assessment |
|---|---|
| cookiecutter-dbt (Datacoves) | dbt structure only — no Docker Compose, no full stack |
| cookiecutter-data-platform | Airflow + dbt + Postgres; pre-dates Iceberg/Trino/MCP; not educational in intent |

Neither is a suitable base. The project's specific profile architecture, pedagogical design, and AI-readiness layer require a purpose-built structure.

### Project Scaffold: Native Tool Composition

**Initialization Sequence:**

```bash
# 1. dbt project skeleton
dbt init local_data_platform

# 2. Install dbt packages
dbt deps

# 3. Docker Compose structure, Makefile, .env.example — hand-crafted
```

**Scaffold Layers:**

| Layer | Tool | Output |
|---|---|---|
| dbt project | `dbt init` | `dbt_project.yml`, `models/`, `tests/`, `macros/`, `seeds/` |
| Docker Compose | Hand-crafted | `docker-compose.yml` with Docker Compose profile blocks |
| Environment config | Hand-crafted | `.env.example` with all required vars documented |
| Makefile | Hand-crafted | Self-documenting targets — `make start`, `make run-pipeline`, `make help` |
| dbt packages | `packages.yml` + `dbt deps` | Elementary, dbt-expectations |
| Python ingestion | Hand-crafted | `ingest/` — dlt scripts + Faker synthetic data generator |

**Verified Package Versions (2026-03-25):**

| Package | Version | Notes |
|---|---|---|
| dbt-core | 1.11.7 | |
| dbt-postgres | 1.10.0 | |
| dbt-trino | 1.10.1 | |
| dbt-duckdb | ≥1.8.x | Requires DuckDB 1.1.x |
| Elementary | 0.20.0+ | |
| dlt | latest | Via PyPI |

Docker images use `latest` tags intentionally (per NFR). Tested adapter/engine combinations documented at implementation time per NFR12.

**dbt Project Structure (post-init, expanded for Medallion):**

```
local-data-platform/
  dbt_project.yml
  packages.yml
  profiles.yml          # env-var driven, profile-agnostic
  models/
    bronze/             # raw, immutable layer
    silver/             # cleaned, deduplicated
    gold/               # marts, serving layer
  macros/               # adapter dispatch macros (Tier 2)
  tests/
  seeds/                # Jaffle Shop seed data
  analyses/
  .env.example
  docker-compose.yml
  Makefile
  ingest/
    faker_generator.py
    dlt_file_source.py
    dlt_api_source.py
```

**Note:** Project initialization (dbt init + directory structure + .env.example + Makefile skeleton) should be the first implementation story (Epic 1, Story 1).

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Repository structure — dbt at repo root
- Schema naming — bronze/silver/gold as database schema names
- Bronze ownership — dlt owns Bronze; dbt reads but never writes to it
- Metadata column convention — dlt native + Silver-level stamps
- Error handling — dedicated `quarantine` schema

**Important Decisions (Shape Architecture):**
- Port allocation map — 18000+ base, increments of 10
- CI/CD scope — maintainer-only; nothing shipped with the template

**Deferred Decisions (Post-MVP):**
- WSL2 compatibility verification — community-confirmed once a Windows user validates
- Terraform scaffold — stretch goal, full profile only, commented-out

### Data Architecture

**Repository Structure**
- Decision: dbt project at repo root (not in subdirectory)
- Rationale: `dbt run` works from repo root without path configuration; lower friction for learners running dbt CLI directly; simpler Docker volume mounts
- Affects: all Makefile targets, Docker volume mounts, `dbt_project.yml` paths

**Schema Naming Convention**
- Decision: Medallion layer names used directly as database schema names — `bronze`, `silver`, `gold`, `quarantine`
- Rationale: Reinforces Medallion terminology consistently across dbt, SQL clients, Lightdash, and documentation; no namespace conflict risk as each profile runs in isolation
- Affects: `dbt_project.yml` schema config, all model paths, SQL client connection docs

**Bronze Layer Ownership**
- Decision: dlt owns and writes the Bronze layer; dbt reads Bronze but never materializes into it
- Rationale: Clean separation of concerns — ingestion tools own raw data, transformation tools own derived data. Enforces Bronze immutability structurally rather than by convention. Aligns with production patterns where the ingestion platform is the system of record for raw data.
- Affects: dbt model scope (Silver + Gold only), ingestion scripts, `dbt_project.yml` model config, learner mental model
- Note: This is itself a teachable architectural decision — document explicitly in README and dbt docs

**Metadata Column Convention**
- Decision: dlt native columns (`_dlt_load_id`, `_dlt_id`) preserved in Bronze as-is; Silver models add `_loaded_at` (dbt run timestamp) and `_source` (source name e.g. `faker_orders_file`)
- Rationale: Learners see authentic dlt column names in Bronze (real production experience) plus explicit transformation-time stamps in Silver that make pipeline stage boundaries tangible
- Affects: all Silver model definitions, `schema.yml` column documentation, Elementary monitoring

**Error/Quarantine Handling**
- Decision: Dedicated `quarantine` schema — failed records from any Silver model land in `quarantine.<model_name>_failed`
- Rationale: Makes failures a first-class, visible architectural concept; learners can query `quarantine.*` immediately after a bad run without knowing which Silver table to check; reinforces Invariant 9 (every failure produces a queryable record)
- Affects: dbt error model pattern, `dbt_project.yml` schema config, observability dashboard queries

### Authentication & Security

- All decisions inherited from PRD and brainstorming session (see Project Context Analysis)
- Three-role RBAC (`engineer_role`, `analyst_role`, `pii_analyst_role`) implemented at engine-native layer (Tier 3) — not in dbt models
- PII masked by default; `pii_analyst_role` requires explicit grant; all PII access logged
- Keycloak for SSO simulation in `full` profile; per-tool local credentials for all others
- Secrets via `.env`; `.env.example` ships with repo; `.gitignore` excludes all `.env` files

### Infrastructure & Deployment

**Port Allocation Map**

| Service | Port | Profile |
|---|---|---|
| Lightdash | 18000 | all |
| Evidence | 18010 | all |
| dbt docs | 18020 | all |
| Elementary dashboard | 18030 | all |
| Postgres | 18040 | postgres |
| MinIO console | 18050 | lakehouse |
| MinIO API | 18060 | lakehouse |
| Trino | 18070 | lakehouse |
| Airflow webserver | 18080 | full |
| OpenMetadata | 18090 | full |
| Prometheus | 18100 | full |
| Grafana | 18110 | full |
| Keycloak | 18120 | full |
| Superset | 18130 | full |
| MCP Server | 18140 | full |

**CI/CD**
- Decision: Minimal maintainer-only CI; nothing shipped with the template
- Rationale: Local-first philosophy — learners run everything locally and should not encounter CI pipeline noise in their forks. Maintainer CI (`dbt compile` + `sqlfluff` + `yamllint` via GitHub Actions) validates template integrity before sharing updates.
- Affects: `.github/workflows/` present in template repo but excluded from what learners are expected to interact with; README notes CI is for maintainer use

### Decision Impact Analysis

**Implementation Sequence:**
1. Repo root structure + `dbt init` + Makefile skeleton + `.env.example` (foundational — everything else depends on this)
2. `bronze`/`silver`/`gold`/`quarantine` schema config in `dbt_project.yml`
3. dlt ingestion scripts writing to `bronze` schema
4. Silver models reading from `bronze`, adding `_loaded_at` and `_source` columns
5. Gold/mart models with dbt contracts enforced
6. Quarantine models for failed record capture
7. Engine-native RBAC per profile (Tier 3, implemented outside dbt)
8. Port allocation applied across `docker-compose.yml`
9. Maintainer CI workflow (`.github/workflows/`)

**Cross-Component Dependencies:**
- Bronze ownership decision means dlt scripts must be implemented and validated before any Silver dbt models can run
- `quarantine` schema must be created in each engine's init script before pipeline runs
- Port map must be consistent across `docker-compose.yml`, README, and `make help` output
- dbt three-tier portability boundary (from Project Context) constrains all Silver/Gold model authoring — Tier 1 portable SQL only in model files

## Implementation Patterns & Consistency Rules

### Critical Conflict Points Identified

8 areas where AI agents could make inconsistent choices without explicit rules:
1. dbt model naming within layer folders
2. SQL style (CTEs vs subqueries, column ordering)
3. schema.yml structure and documentation completeness
4. Metadata column naming and placement in Silver models
5. Makefile target naming and documentation format
6. Environment variable naming conventions
7. Docker service naming in Compose files
8. Python script style (ingestion scripts)

---

### Naming Patterns

**dbt Model Naming**
- Models are named without layer prefixes — the schema (folder) provides the layer context
- ✅ `models/silver/orders.sql` → materializes as `silver.orders`
- ❌ `models/silver/stg_orders.sql` — prefix redundant when folder = layer
- Source staging models: `{source}_{entity}.sql` e.g. `faker_orders.sql`, `faker_customers.sql`
- Mart/Gold models: `{entity}_mart.sql` or `fct_{entity}.sql` / `dim_{entity}.sql` for fact/dimension distinction
- Quarantine models: `{source_model}_failed.sql` in `models/quarantine/`

**SQL Column Naming**
- Always `snake_case` — required for cross-engine compatibility (Trino is case-sensitive)
- Boolean columns: `is_` prefix — `is_deleted`, `is_active`, `is_pii`
- Timestamp columns: `_at` suffix — `created_at`, `loaded_at`, `updated_at`
- ID columns: `_id` suffix — `order_id`, `customer_id`
- Foreign keys: `{referenced_entity}_id` — `customer_id` not `fk_customer`
- ❌ Never use reserved words as column names across all three engines (check DuckDB + Postgres + Trino lists)

**Metadata Column Names (Silver layer — consistent across all Silver models)**
```sql
_dlt_load_id    -- inherited from Bronze (dlt native, do not rename)
_dlt_id         -- inherited from Bronze (dlt native, do not rename)
_loaded_at      -- CURRENT_TIMESTAMP at Silver dbt run time
_source         -- string literal identifying source e.g. 'faker_orders_file'
```

**Environment Variable Naming**
- `SCREAMING_SNAKE_CASE` throughout
- Prefixed by service: `DBT_`, `LIGHTDASH_`, `AIRFLOW_`, `POSTGRES_`, `MINIO_`, `TRINO_`, `KEYCLOAK_`
- Profile selector: `COMPOSE_PROFILES` (Docker Compose native)
- ✅ `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- ❌ `DB_HOST`, `host`, `postgresHost` — inconsistent prefixing causes confusion

**Docker Service Naming**
- `lowercase-hyphenated` matching the tool name
- ✅ `lightdash`, `dbt`, `minio`, `trino`, `airflow-webserver`, `airflow-scheduler`
- ❌ `Lightdash`, `dbt_service`, `airflowWebserver`

**Makefile Target Naming**
- `kebab-case` for all targets
- ✅ `make run-pipeline`, `make open-docs`, `make load-data`
- ❌ `make run_pipeline`, `make runPipeline`
- Every target must have a `##` comment on the same line for `make help` auto-documentation:
```makefile
run-pipeline: ## Run full pipeline: ingestion → dbt run → dbt test
```

**Python Script Naming**
- `snake_case` for all files, functions, variables
- Ingestion scripts: `{tool}_{source_type}_source.py` e.g. `dlt_file_source.py`, `dlt_api_source.py`
- Generator scripts: `{dataset}_generator.py` e.g. `faker_generator.py`

---

### Structure Patterns

**dbt Model Organisation**
```
models/
  bronze/         # READ-ONLY reference models (sources only — no materializations)
  silver/
    {source}/     # group by source system e.g. silver/faker/
  gold/
    facts/        # fct_ models
    dimensions/   # dim_ models
    marts/        # {domain}_mart.sql
  quarantine/     # {source_model}_failed.sql — one per Silver model
  metrics/        # MetricFlow semantic layer definitions
```

**dbt Source Declarations**
- All Bronze tables declared as dbt sources in `models/bronze/sources.yml`
- Source name matches the dlt pipeline name: `source('faker', 'orders')`
- One `sources.yml` per source system — not one global file

**schema.yml Documentation Completeness Rule**
- Every model must have: `description`, at least one `test`, and all columns documented
- Every column must have: `description`, `data_type`, and `meta.pii: true/false`
- Gold/mart models must additionally have: `constraints` block (dbt contract enforcement)
- ❌ A story is not complete if any model or column lacks description or pii tag

**Test Organisation**
- Generic tests (unique, not_null, relationships, accepted_values): declared in `schema.yml`
- Extended tests (dbt-expectations): declared in `schema.yml`
- Singular tests (custom SQL assertions): `tests/` directory at root
- Elementary anomaly detection: configured in `schema.yml` via `elementary` meta block

---

### Format Patterns

**SQL Style**
- CTEs first — no inline subqueries in production models
- One CTE per logical transformation step, named descriptively
- Final `SELECT` is the last statement, selecting from the last CTE
```sql
-- ✅ Correct pattern
WITH source AS (
    SELECT * FROM {{ source('faker', 'orders') }}
),
renamed AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        CURRENT_TIMESTAMP AS _loaded_at,
        'faker_orders_file' AS _source,
        _dlt_load_id,
        _dlt_id
    FROM source
)
SELECT * FROM renamed

-- ❌ Avoid
SELECT order_id, (SELECT customer_name FROM customers WHERE id = o.customer_id) ...
```

**Timestamp Handling**
- Always UTC — no local timezone storage
- `CURRENT_TIMESTAMP` for run-time stamps (cross-engine compatible)
- Store as `TIMESTAMP` type — not `VARCHAR`, not epoch integers
- Column suffix: `_at` (not `_date` unless it's a true DATE type)

**YAML Formatting**
- 2-space indentation throughout (dbt project files, Docker Compose, schema.yml)
- String values quoted only when containing special characters
- Lists use `- ` prefix, not inline `[a, b, c]` format in schema.yml

**Jinja in SQL**
- `{{ ref('model_name') }}` and `{{ source('source', 'table') }}` — always use, never hardcode schema.table
- Macros in `macros/` only — no inline `{% macro %}` blocks in model files
- Adapter dispatch macros follow dbt convention: `macros/adapters/{macro_name}.sql`

---

### Process Patterns

**Incremental Model Pattern (Silver)**
- Strategy: `delete+insert` as default (works across DuckDB, Postgres, Trino)
- Unique key: `_dlt_id` (dlt's row-level hash — stable across reruns)
- Always include `is_incremental()` guard:
```sql
{{ config(materialized='incremental', unique_key='_dlt_id', incremental_strategy='delete+insert') }}
...
{% if is_incremental() %}
WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})
{% endif %}
```

**Quarantine Pattern**
- Every Silver model has a corresponding quarantine model
- Quarantine model captures records that fail validation rules
- Quarantine schema: `quarantine.{source_model}_failed`
- Quarantine records include: original row + `_failed_reason` (string) + `_failed_at` (timestamp)

**Error Handling in Python (dlt scripts)**
- All dlt pipelines wrapped in try/except
- Failures logged to stdout with structured format: `{"level": "ERROR", "pipeline": "...", "error": "..."}`
- Exit code 1 on failure (so Makefile and cron detect failures)
- Never silently swallow exceptions

**dbt Tag Usage**
- Models tagged by layer: `tags: ['bronze']`, `tags: ['silver']`, `tags: ['gold']`
- Enables selective runs: `dbt run --select tag:silver`
- Additional tags for profile-specific models: `tags: ['lakehouse-only']`

---

### Enforcement Guidelines

**All AI Agents MUST:**
- Use `snake_case` for all SQL column names — no exceptions
- Document every model and column in `schema.yml` before marking a story complete
- Use `{{ ref() }}` and `{{ source() }}` — never hardcode schema.table in SQL
- Add `_loaded_at` and `_source` to every Silver model
- Use CTEs, not subqueries, in all production models
- Prefix all environment variables with the service name
- Add `##` documentation comment to every Makefile target
- Never write dbt materializations into the `bronze` schema

**Pattern Verification:**
- `dbt compile` catches ref/source errors and Jinja issues
- `sqlfluff lint` enforces SQL style (CTE-first, snake_case)
- `yamllint` catches YAML formatting issues
- `dbt test` validates schema.yml test completeness post-implementation

**Anti-Patterns to Avoid:**
- ❌ Hardcoding `bronze.orders` instead of `{{ source('faker', 'orders') }}`
- ❌ Adding `stg_` or `raw_` prefixes to model names (layer folder provides context)
- ❌ Storing timestamps as VARCHAR or epoch integers
- ❌ Writing a Silver model without a corresponding quarantine model
- ❌ Using engine-specific SQL syntax in Tier 1 models (e.g. DuckDB-only functions)
- ❌ Environment variables without service prefix (`DB_HOST` instead of `POSTGRES_HOST`)
- ❌ Makefile targets without `##` documentation comments

## Project Structure & Boundaries

### Complete Project Directory Structure

```
local-data-platform/
├── README.md
├── .env.example                    # All required env vars documented
├── .gitignore                      # Excludes .env, dbt target/, logs/
├── Makefile                        # Learner UX — all targets self-documenting via ##
├── requirements.txt                # Python deps for running ingest scripts locally
│
├── dbt_project.yml                 # dbt project root at repo root (Decision 1)
├── packages.yml                    # Elementary, dbt-expectations
├── profiles.yml                    # Env-var driven — reads COMPOSE_PROFILES, adapter vars
│
├── models/
│   ├── bronze/
│   │   ├── sources.yml             # ALL Bronze tables declared as dbt sources here
│   │   └── .gitkeep               # No SQL models — dlt owns this layer
│   ├── silver/
│   │   └── faker/                  # Grouped by source system
│   │       ├── schema.yml          # All Silver models + columns documented
│   │       ├── faker_orders.sql
│   │       ├── faker_customers.sql
│   │       ├── faker_products.sql
│   │       └── faker_returns.sql
│   ├── gold/
│   │   ├── facts/
│   │   │   ├── schema.yml          # dbt contracts enforced here
│   │   │   └── fct_orders.sql
│   │   ├── dimensions/
│   │   │   ├── schema.yml          # dbt contracts enforced here
│   │   │   ├── dim_customers.sql
│   │   │   └── dim_products.sql
│   │   └── marts/
│   │       ├── schema.yml          # dbt contracts enforced here
│   │       └── orders_mart.sql
│   ├── quarantine/
│   │   ├── schema.yml
│   │   ├── faker_orders_failed.sql
│   │   ├── faker_customers_failed.sql
│   │   ├── faker_products_failed.sql
│   │   └── faker_returns_failed.sql
│   └── metrics/                    # MetricFlow semantic layer definitions
│       ├── schema.yml
│       ├── orders.yml              # MetricFlow metric definitions
│       └── customers.yml
│
├── macros/
│   ├── generate_schema_name.sql    # Custom schema routing (bronze/silver/gold/quarantine)
│   └── adapters/
│       └── incremental_strategy.sql  # Tier 2 adapter dispatch macros
│
├── tests/                          # Singular SQL tests (custom assertions)
│   └── assert_no_quarantine_overflow.sql
│
├── seeds/                          # Jaffle Shop onboarding data
│   ├── jaffle_shop_orders.csv
│   ├── jaffle_shop_customers.csv
│   └── schema.yml
│
├── analyses/                       # Exploratory SQL — not materialized
│   └── layer_row_counts.sql
│
├── ingest/
│   ├── faker_generator.py          # Synthetic e-commerce data generator (Faker)
│   ├── dlt_file_source.py          # dlt pipeline: file drop → bronze
│   ├── dlt_api_source.py           # dlt pipeline: REST API → bronze
│   └── requirements.txt            # dlt, faker, etc.
│
├── data/                           # Sample source data files (file-source ingestion)
│   ├── products/
│   │   └── products_sample.json
│   └── README.md
│
├── docker/
│   ├── dbt/
│   │   └── Dockerfile              # dbt + adapters container
│   ├── init/
│   │   ├── postgres_init.sql       # Create roles, schemas, RLS policies (postgres profile)
│   │   ├── trino_init.sql          # Create schemas, access control (lakehouse profile)
│   │   └── duckdb_init.sql         # Create schemas (simple profile — limited RBAC)
│   ├── mcp/
│   │   └── Dockerfile              # MCP server wrapping MetricFlow (full profile)
│   ├── airflow/
│   │   ├── Dockerfile              # Custom Airflow image with dbt + dlt (full profile)
│   │   └── dags/
│   │       └── pipeline_dag.py     # Main pipeline DAG
│   └── superset/
│       └── init.sh                 # Superset bootstrap (admin user, DB init)
│
├── docker-compose.yml              # All profiles — simple, postgres, lakehouse, lakehouse-spark, full
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # Maintainer CI: dbt compile + sqlfluff + yamllint
│
├── docs/
│   ├── cloud-equivalence.md        # Local → cloud component mapping table (FR46)
│   ├── open-table-formats.md       # Iceberg vs Delta Lake vs Hudi reference (FR47)
│   ├── profile-guide.md            # Per-profile hardware requirements and service list
│   ├── wsl2.md                     # WSL2 compatibility notes (FR48)
│   ├── rbac-guide.md               # Three-role RBAC — how it works per engine
│   └── mcp-connection.md           # MCP server connection instructions (FR42)
│
└── terraform/                      # Stretch goal — commented-out scaffold (full profile)
    └── README.md
```

### Architectural Boundaries

**Ingestion Boundary (dlt → Bronze)**
- dlt scripts in `ingest/` write exclusively to the `bronze` schema
- dbt has zero write access to `bronze` — read-only via `{{ source() }}` references
- Bronze tables are append-only; dlt's native `_dlt_load_id` and `_dlt_id` columns are the authoritative row identity
- Boundary enforced structurally: no `.sql` model files exist under `models/bronze/`

**Transformation Boundary (Bronze → Silver → Gold)**
- Silver reads from `{{ source('faker', ...) }}` — never from `{{ ref() }}` of a Bronze model
- Gold reads from `{{ ref('silver_model') }}` only — never directly from sources
- Quarantine models read from Silver CTEs — capture failed records before Silver materializes clean data
- dbt contracts (`constraints:` block) enforced on all Gold models — breaking schema changes fail explicitly

**Semantic Layer Boundary (Gold → MetricFlow → Consumers)**
- MetricFlow metric definitions in `models/metrics/` reference Gold models only
- BI tools connect to the warehouse directly for ad-hoc SQL; MetricFlow definitions are the canonical source for named metrics
- MCP Server wraps MetricFlow API — AI agents never query Gold tables directly (Invariant 13)
- RBAC enforced at the warehouse/engine layer (Tier 3) — MCP Server inherits `analyst_role` credentials by default

**Engine-Native Boundary (Tier 3)**
- `docker/init/` scripts contain all RBAC, schema creation, PII masking config — per engine
- These are the only files that contain engine-specific SQL
- dbt model files (`models/**/*.sql`) must contain only Tier 1 portable SQL

### Requirements to Structure Mapping

| FR Category | Primary Location |
|---|---|
| Environment & Profile Management (FR1–7) | `docker-compose.yml`, `Makefile`, `.env.example`, `profiles.yml` |
| Data Ingestion (FR8–12) | `ingest/`, `data/`, `docker/init/` (schema creation) |
| Data Transformation (FR13–17) | `models/silver/`, `models/gold/`, `models/quarantine/`, `macros/` |
| Data Quality & Observability (FR18–23) | `schema.yml` files (all layers), `tests/`, `packages.yml` |
| Data Access & Serving (FR24–30) | `models/metrics/`, `docs/mcp-connection.md`, warehouse native |
| Access Control & Governance (FR31–38) | `docker/init/`, `schema.yml` meta/tags, `docs/rbac-guide.md` |
| AI Agent Access (FR39–42) | `docker/mcp/`, `models/metrics/`, `docs/mcp-connection.md` |
| Alerting (FR43–44) | `schema.yml` Elementary config, `docker/airflow/dags/` |
| Documentation & Discoverability (FR45–49) | `README.md`, `docs/`, generated dbt docs, `Makefile` help |

### Integration Points

**Internal Data Flow**
```
faker_generator.py / dlt_file_source.py / dlt_api_source.py
    → bronze schema (dlt writes)
        → models/silver/faker/*.sql (dbt reads via source())
            → models/gold/**/*.sql (dbt reads via ref())
            → models/quarantine/*_failed.sql (failed records)
                → models/metrics/*.yml (MetricFlow reads Gold)
                    → Lightdash / Evidence / Superset (direct warehouse connection)
                    → docker/mcp/ (MCP Server wraps MetricFlow API)
```

**Observability Flow**
```
dbt run → target/run_results.json + target/manifest.json + target/catalog.json
    → Elementary (reads artifacts → anomaly detection, freshness, schema changes)
    → OpenMetadata (reads manifest + catalog → cross-system lineage)
    → Prometheus (dbt artifacts parsed → metrics pushed) [full profile]
    → Grafana (Prometheus datasource → unified ops dashboard) [full profile]
```

**Orchestration Flow (full profile)**
```
Airflow DAG (docker/airflow/dags/pipeline_dag.py)
    → BashOperator: python ingest/dlt_file_source.py
    → BashOperator: python ingest/dlt_api_source.py
    → BashOperator: dbt run --select tag:silver
    → BashOperator: dbt test --select tag:silver
    → BashOperator: dbt run --select tag:gold
    → BashOperator: dbt test --select tag:gold
    → BashOperator: edr send-report (Elementary alert)
```

### Development Workflow Integration

**Local development (all profiles)**
```bash
make start          # docker compose --profile $COMPOSE_PROFILES up -d
make load-data      # python ingest/faker_generator.py && python ingest/dlt_file_source.py
make run-pipeline   # dbt run && dbt test
make open-docs      # open Lightdash (:18000), dbt docs (:18020), Elementary (:18030)
make stop           # docker compose down
```

**Profile switching**
- Edit `.env` → change `COMPOSE_PROFILES=simple` to `COMPOSE_PROFILES=lakehouse`
- `make stop && make start` — no code changes required
- `profiles.yml` reads adapter vars from `.env` — dbt automatically uses correct engine

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- dbt at root + env-var `profiles.yml` + Docker Compose profiles — coherent, no path conflicts
- dlt owns Bronze / dbt reads only — structurally enforced (no `.sql` files in `models/bronze/`)
- `delete+insert` incremental strategy — verified compatible with DuckDB, Postgres, and Trino
- `_dlt_id` as unique key — dlt's stable row hash, cross-engine safe
- MetricFlow included in dbt-core 1.6+ — confirmed compatible with dbt-core 1.11.7
- Elementary 0.20.0+ — confirmed compatible with dbt-core 1.11.7
- RBAC in `docker/init/` (Tier 3) + PII tags in `schema.yml` (portable declaration) — coherent separation

**Pattern Consistency:**
- `snake_case` columns + cross-engine Trino case-sensitivity requirement — consistent and enforced
- No layer prefixes in model names + folder = layer convention — consistent throughout
- CTE-first SQL + quarantine pattern — consistent, complementary
- `kebab-case` Makefile targets + `SCREAMING_SNAKE_CASE` env vars — consistent within their respective domains

**Structure Alignment:**
- `models/bronze/` contains no `.sql` files — aligned with dlt-owns-Bronze decision
- `docker/init/` is the only location for engine-specific SQL — Tier 3 boundary respected
- All 49 FRs mapped to specific files/directories — complete alignment

### Requirements Coverage Validation ✅

**Functional Requirements — All 49 FRs covered:**

| Category | Status | Notes |
|---|---|---|
| Environment & Profile Management (FR1–7) | ✅ | `docker-compose.yml`, `Makefile`, `.env.example`, `profiles.yml` |
| Data Ingestion (FR8–12) | ✅ | `ingest/`, `data/`, `docker/init/` |
| Data Transformation (FR13–17) | ✅ | `models/silver/`, `gold/`, `quarantine/`, `macros/` |
| Data Quality & Observability (FR18–23) | ✅ | `schema.yml` files, `tests/`, Elementary via `packages.yml` |
| Data Access & Serving (FR24–30) | ✅ | `models/metrics/`, warehouse-native, `docs/mcp-connection.md` |
| Access Control & Governance (FR31–38) | ✅ | `docker/init/`, `schema.yml` meta/tags, `docs/rbac-guide.md` |
| AI Agent Access (FR39–42) | ✅ | `docker/mcp/`, `models/metrics/`, MetricFlow enforcement |
| Alerting (FR43–44) | ✅ | Elementary config in `schema.yml`, Airflow DAG alerts |
| Documentation & Discoverability (FR45–49) | ✅ | `README.md`, `docs/`, dbt docs, `Makefile` help |

**Non-Functional Requirements — All 21 NFRs covered:**

| Category | Status | Notes |
|---|---|---|
| Performance (NFR1–5) | ✅ | Local-first architecture; simple profile minimal footprint; implementation-dependent |
| Security (NFR6–9) | ✅ | `.env` excluded, `.env.example` ships, PII masking via Tier 3, IAM docs |
| Integration (NFR10–14) | ✅ | Docker Compose v2, ARM64 flagged as hard gate, adapter versions verified |
| Reliability (NFR15–18) | ✅ | Idempotency via `delete+insert`, clean cold-start, profile isolation in Compose |
| Maintainability (NFR19–21) | ✅ | `.env` isolation, shared dbt project, `make help` self-documenting |

### Implementation Readiness Validation ✅

**Decision Completeness:** 7 core decisions documented with rationale and affected components. dbt ecosystem versions verified (2026-03-25). ARM64 validation deferred to per-service implementation check (per PRD risk mitigation).

**Structure Completeness:** Complete directory tree defined. All files named. Integration points, data flows, and orchestration flows documented.

**Pattern Completeness:** 8 conflict points addressed. Naming, structure, format, and process patterns defined with examples and anti-patterns.

### Gap Analysis Results

**Important Gap — Jaffle Shop seeds vs Bronze layer consistency:**
- `seeds/jaffle_shop_*.csv` loaded via `dbt seed` bypasses Bronze/dlt entirely
- Inconsistent with the Bronze-owns-raw-data architectural boundary (Invariant 8)
- **Resolution:** Document explicitly in README and dbt docs that Jaffle Shop seeds are an onboarding-only shortcut. Seeds land in a `seeds` schema, not `bronze`. The Faker dataset follows the canonical Bronze → Silver → Gold path. This distinction is pedagogically intentional — learners see the simplified seed pattern first, then the full ingestion pattern.
- Label seeds models clearly in `schema.yml`: `meta: {layer: 'seed', pattern: 'onboarding-only'}`

**Minor Gap — dbt project name:**
- `dbt init` rejects hyphens in project names
- `dbt_project.yml` must use `name: 'local_data_platform'` (underscored)
- Repository directory remains `local-data-platform` (hyphenated) — no conflict
- Document this discrepancy in `dbt_project.yml` comments

**Minor Gap — C4 / sequence diagrams:**
- Brainstorming session listed C4 context/container/component diagrams and sequence diagrams as Priority 1 outputs
- Not in scope for this architecture decision document — these are visualisation artefacts
- **Resolution:** Create as a separate `docs/architecture-diagrams.md` deliverable post this workflow

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed (49 FRs, 21 NFRs, 9 categories)
- [x] Scale and complexity assessed (Medium-High)
- [x] Technical constraints identified (ARM64, .env isolation, Docker Compose v2)
- [x] Cross-cutting concerns mapped (8 concerns)
- [x] dbt three-tier portability boundary established

**✅ Architectural Decisions**
- [x] 7 core decisions documented with rationale
- [x] Technology stack fully specified with verified versions
- [x] Integration patterns defined (ingestion, transformation, semantic layer, observability)
- [x] Performance and reliability considerations addressed (idempotency, cold-start)

**✅ Implementation Patterns**
- [x] Naming conventions established (SQL columns, models, env vars, Docker services, Makefile)
- [x] Structure patterns defined (model organisation, source declarations, test placement)
- [x] Format patterns specified (SQL style, timestamps, YAML, Jinja)
- [x] Process patterns documented (incremental strategy, quarantine, error handling, tags)
- [x] Enforcement guidelines and anti-patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined with all files named
- [x] Component boundaries established (ingestion, transformation, semantic layer, engine-native)
- [x] Integration points mapped (data flow, observability flow, orchestration flow)
- [x] All 49 FRs mapped to specific locations

### Architecture Readiness Assessment

**Overall Status: READY FOR IMPLEMENTATION**

**Confidence Level: High** — all decisions are specific, all patterns have examples, all FRs are mapped to concrete locations. The three gaps are documentation clarifications, not missing capabilities.

**Key Strengths:**
1. Bronze layer boundary is structurally enforced (no SQL files in `models/bronze/`) — impossible to accidentally violate
2. dbt three-tier portability constraint is explicit and documented — agents know exactly where the line is
3. Quarantine as a first-class schema makes failure handling non-optional
4. MetricFlow as the mandatory AI/BI interface is architecturally enforced, not just documented
5. All 16 invariants from the brainstorming session are traceable to specific architectural decisions

**Areas for Future Enhancement:**
- C4 and sequence diagrams (`docs/architecture-diagrams.md`)
- ARM64 compatibility matrix as services are validated
- NYC Taxi dataset integration (Phase 2 — requires additional `models/silver/nyc_taxi/` folder)
- Spark profile additions (`models/` tagging for `lakehouse-spark` only models)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented in this document
- Use implementation patterns consistently — refer to the Enforcement Guidelines before writing any SQL, YAML, or Python
- Respect the dbt three-tier boundary — Tier 1 portable SQL in model files only
- Never materialise into `bronze` schema — dlt owns it
- Every Silver model requires a corresponding quarantine model before the story is complete
- Every model and column must be documented in `schema.yml` before marking a story complete

**First Implementation Story:**
```bash
# Epic 1, Story 1 — Project scaffold
dbt init local_data_platform   # Note: underscore, not hyphen
# Then: rename generated folder contents to repo root
# Then: create Makefile, .env.example, docker-compose.yml skeleton
# Then: configure dbt_project.yml with bronze/silver/gold/quarantine schema routing
# Then: implement generate_schema_name macro (critical — all schema routing depends on this)
```
