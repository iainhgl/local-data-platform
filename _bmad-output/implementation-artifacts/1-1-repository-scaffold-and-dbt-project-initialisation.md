# Story 1.1: Repository Scaffold and dbt Project Initialisation

Status: done

## Story

As a data engineer,
I want a cloneable repository with a dbt project skeleton, Makefile, and `.env.example` already in place,
so that I can start from a working structure without manual setup steps.

## Acceptance Criteria

1. **Given** I have cloned the repository and have Docker Desktop running, **When** I run `make help`, **Then** all available Makefile targets are listed with descriptions with no errors, **And** the output includes at minimum `start`, `stop`, `run-pipeline`, `open-docs`, and `help` targets.

2. **Given** the repository is freshly cloned, **When** I inspect the root directory, **Then** `dbt_project.yml`, `profiles.yml`, `packages.yml`, `Makefile`, `.env.example`, `.gitignore`, and `docker-compose.yml` are all present at repo root, **And** `.env` is absent (excluded by `.gitignore`).

3. **Given** I copy `.env.example` to `.env`, **When** I inspect `.env.example`, **Then** all required environment variables are documented with placeholder values and inline comments, **And** no real credentials, secrets, or API keys are present.

4. **Given** the dbt project skeleton exists, **When** I inspect the directory structure, **Then** `models/bronze/`, `models/silver/`, `models/gold/`, `models/quarantine/`, `models/metrics/`, `macros/`, `tests/`, `seeds/`, `analyses/`, `ingest/`, `data/`, `docker/`, `docs/`, `terraform/` are all present, **And** `models/bronze/` contains only `sources.yml` and `.gitkeep` — no `.sql` model files.

## Tasks / Subtasks

- [x] Task 1: Create directory skeleton (AC: 4)
  - [x] Create `models/bronze/`, `models/silver/`, `models/gold/` with `facts/`, `dimensions/`, `marts/` subdirs, `models/quarantine/`, `models/metrics/`
  - [x] Create `macros/adapters/`, `tests/`, `seeds/`, `analyses/`
  - [x] Create `ingest/`, `data/`, `docker/`, `docs/`, `terraform/`
  - [x] Add `.gitkeep` to every empty directory that must be git-tracked
  - [x] Create `models/bronze/sources.yml` as empty placeholder and `models/bronze/.gitkeep`
  - [x] VERIFY: zero `.sql` files exist anywhere under `models/bronze/`

- [x] Task 2: Create `dbt_project.yml` (AC: 2, 4)
  - [x] Set `name: local_data_platform`, `version: '1.0.0'`
  - [x] Set `profile: local_data_platform`
  - [x] Configure `model-paths`, `seed-paths`, `test-paths`, `analysis-paths`, `macro-paths` — all relative to repo root
  - [x] Under `models.local_data_platform`, configure per-folder schema and materialization (see Dev Notes)
  - [x] Ensure NO `bronze` block — Bronze is a source, not a model materialization
  - [x] Add layer tags per folder: `silver` → `['silver']`, `gold` → `['gold']`, `quarantine` → `['quarantine']`, `metrics` → `['metrics']`

- [x] Task 3: Create `profiles.yml` — fully env-var driven (AC: 2)
  - [x] DuckDB profile reading `DBT_DUCKDB_PATH` env var
  - [x] Postgres profile reading all `POSTGRES_*` env vars
  - [x] Trino profile reading all `TRINO_*` env vars
  - [x] Active target selected by `COMPOSE_PROFILES` env var
  - [x] No hardcoded connection values anywhere in the file

- [x] Task 4: Create `packages.yml` (AC: 2)
  - [x] `dbt-labs/dbt_utils` latest
  - [x] `elementary-data/elementary` ≥0.20.0
  - [x] `calogica/dbt_expectations` latest

- [x] Task 5: Create `.env.example` with all required variables (AC: 2, 3)
  - [x] `COMPOSE_PROFILES` with comment explaining options
  - [x] All `DBT_` vars for DuckDB
  - [x] All `POSTGRES_` vars (HOST, PORT, USER, PASSWORD, DB)
  - [x] All `MINIO_` vars (ROOT_USER, ROOT_PASSWORD, ENDPOINT)
  - [x] All `TRINO_` vars (HOST, PORT, USER)
  - [x] All `LIGHTDASH_` vars (SECRET_KEY)
  - [x] Every variable has inline `#` comment explaining purpose and expected format
  - [x] Zero real credentials — all placeholder values

- [x] Task 6: Create `.gitignore` (AC: 2)
  - [x] Exclude `.env` and all variants EXCEPT `.env.example`
  - [x] Exclude `target/`, `dbt_packages/`, `logs/`
  - [x] Exclude Python caches: `__pycache__/`, `*.pyc`, `*.pyo`, `.venv/`, `venv/`
  - [x] Exclude OS files: `.DS_Store`, `Thumbs.db`

- [x] Task 7: Create `Makefile` — `make help` must work immediately (AC: 1)
  - [x] `help` target: auto-documents all `##`-annotated targets using `grep + awk` pattern
  - [x] `start` target: stub with `## Start all services for the active COMPOSE_PROFILES`
  - [x] `stop` target: stub with `## Stop all running services`
  - [x] `run-pipeline` target: stub with `## Run full pipeline: ingestion → dbt run → dbt test`
  - [x] `open-docs` target: stub with `## Open dbt docs and Elementary dashboard in browser`
  - [x] `install` target: `## Install dbt packages (dbt deps)` — can call `dbt deps` now
  - [x] All targets use `kebab-case`; every target has `##` comment on the same line
  - [x] VERIFY: `make help` runs without error and lists all targets

- [x] Task 8: Create `docker-compose.yml` scaffold (AC: 2)
  - [x] Use Docker Compose v2 `services:` structure (no `version:` key required in v2)
  - [x] Define profile blocks: `simple`, `postgres`, `lakehouse`, `full`
  - [x] Service names in `lowercase-hyphenated` format
  - [x] Add `platform: linux/arm64` to all services (ARM64 requirement)
  - [x] Include Lightdash port stub `18000:3000` in `simple` profile
  - [x] Full port map (all 15 services) is delivered in Story 1.3 — this scaffold only needs at least one service per profile as placeholder

- [x] Task 9: Create `requirements.txt` (AC: 2)
  - [x] `dlt`
  - [x] `faker`
  - [x] `pandas`

- [x] Task 10: Create `README.md` stub (AC: 2)
  - [x] Project title: `local-data-platform`
  - [x] One-line description
  - [x] `## Quick Start` placeholder (content added in Story 2.14)
  - [x] `## Hardware Requirements` section: 8GB RAM minimum (simple/postgres), 16GB recommended (lakehouse/full)

- [x] Task 11: Create `.github/workflows/ci.yml` (AC: 2)
  - [x] Maintainer-only CI: `dbt compile` + `sqlfluff` + `yamllint`
  - [x] Triggers: `push` to `main`, `pull_request` to `main`
  - [x] README comment: "CI is for maintainer use; learners do not need to interact with it"

- [x] Task 12: Final verification (AC: 1, 2, 3, 4)
  - [x] `make help` outputs all required targets with descriptions, exit code 0
  - [x] All root files present: `dbt_project.yml`, `profiles.yml`, `packages.yml`, `Makefile`, `.env.example`, `.gitignore`, `docker-compose.yml`
  - [x] `.env` absent from repo
  - [x] All directories present; `models/bronze/` has only `sources.yml` and `.gitkeep`

### Review Findings

- [x] [Review][Patch] `full` profile selects a nonexistent dbt target [`profiles.yml:3`]
- [x] [Review][Patch] CI masks lint failures and can report green when checks fail [`.github/workflows/ci.yml:36`]

## Dev Notes

### Critical Architecture Constraints

**dbt at Repo Root — Non-Negotiable**
- `dbt_project.yml` lives at the repository root, NOT in a subdirectory
- `dbt run` must work from `./` without `--project-dir` flags
- All Makefile targets and Docker volume mounts depend on this root placement
- [Source: architecture.md#Data Architecture — Repository Structure]

**Bronze Layer: NO SQL Models — Ever**
- `models/bronze/` = ONLY `sources.yml` + `.gitkeep`. Zero `.sql` files.
- dlt owns and writes the Bronze schema. dbt reads Bronze via `{{ source() }}` only.
- This is structurally enforced by leaving the folder empty of SQL models.
- Adding any `.sql` file to `models/bronze/` is a critical violation of the architecture.
- [Source: architecture.md#Bronze Layer Ownership]

**Schema Names = Medallion Layer Names**
- `bronze`, `silver`, `gold`, `quarantine` are the actual database schema names.
- Configured in `dbt_project.yml` via `+schema:` per layer folder.
- No `bronze` block in `dbt_project.yml` — bronze tables are created by dlt.
- [Source: architecture.md#Schema Naming Convention]

### dbt_project.yml — Required Configuration

```yaml
name: local_data_platform
version: '1.0.0'
profile: local_data_platform

model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]
analysis-paths: ["analyses"]
macro-paths: ["macros"]

target-path: "target"
clean-targets: ["target", "dbt_packages"]

models:
  local_data_platform:
    silver:
      +schema: silver
      +materialized: incremental
      +tags: ['silver']
    gold:
      +schema: gold
      +materialized: table
      +tags: ['gold']
    quarantine:
      +schema: quarantine
      +materialized: incremental
      +tags: ['quarantine']
    metrics:
      +schema: metrics
      +materialized: table
      +tags: ['metrics']
```

No `bronze:` block. Bronze is a source, not a materialization target.

### Makefile — make help Pattern

```makefile
.PHONY: help start stop run-pipeline open-docs install

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

start: ## Start all services for the active COMPOSE_PROFILES
	@echo "Profile: $${COMPOSE_PROFILES} — service lifecycle implemented in Story 1.2"

stop: ## Stop all running services
	@echo "Service lifecycle implemented in Story 1.2"

run-pipeline: ## Run full pipeline: ingestion → dbt run → dbt test
	@echo "Pipeline implementation in Story 2"

open-docs: ## Open dbt docs and Elementary dashboard in browser
	@echo "Implementation in Story 2"

install: ## Install dbt packages (dbt deps)
	dbt deps
```

- `kebab-case` targets — required
- `##` comment on every target — required for `make help` auto-documentation (NFR21)
- `make help` must produce formatted output with exit code 0 immediately (AC-1 gate)

### profiles.yml — Env-Var Driven

```yaml
local_data_platform:
  target: "{{ env_var('COMPOSE_PROFILES', 'simple') }}"
  outputs:
    simple:
      type: duckdb
      path: "{{ env_var('DBT_DUCKDB_PATH', 'dev.duckdb') }}"
      threads: 4
    postgres:
      type: postgres
      host: "{{ env_var('POSTGRES_HOST', 'localhost') }}"
      port: "{{ env_var('POSTGRES_PORT', '18040') | int }}"
      user: "{{ env_var('POSTGRES_USER', 'dbt') }}"
      password: "{{ env_var('POSTGRES_PASSWORD', '') }}"
      dbname: "{{ env_var('POSTGRES_DB', 'local_data_platform') }}"
      schema: silver
      threads: 4
    lakehouse:
      type: trino
      host: "{{ env_var('TRINO_HOST', 'localhost') }}"
      port: "{{ env_var('TRINO_PORT', '18070') | int }}"
      user: "{{ env_var('TRINO_USER', 'trino') }}"
      database: iceberg
      schema: silver
      threads: 4
```

`COMPOSE_PROFILES` is the single variable that controls both Docker Compose profile activation and the dbt target adapter — single source of truth for profile switching (FR3).

### .env.example — Required Variables

```bash
# Profile selector — controls both Docker Compose services and dbt adapter
# Options: simple | postgres | lakehouse | full
COMPOSE_PROFILES=simple

# DuckDB (simple profile)
# Path to DuckDB database file, relative to repo root
DBT_DUCKDB_PATH=dev.duckdb

# Postgres (postgres profile)
POSTGRES_HOST=localhost
POSTGRES_PORT=18040
POSTGRES_USER=dbt
POSTGRES_PASSWORD=changeme
POSTGRES_DB=local_data_platform

# MinIO — object storage (lakehouse profile)
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=changeme
MINIO_ENDPOINT=http://localhost:18060

# Trino — query engine (lakehouse profile)
TRINO_HOST=localhost
TRINO_PORT=18070
TRINO_USER=trino

# Lightdash — BI dashboard
LIGHTDASH_SECRET_KEY=changeme-generate-a-random-string
```

All values are placeholders. `changeme` strings are clearly not real credentials. No tokens, API keys, or secrets.

### .gitignore — Required Entries

```gitignore
# Environment — NEVER commit .env files
.env
.env.*
!.env.example

# dbt build artifacts
target/
dbt_packages/
logs/

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/

# OS
.DS_Store
Thumbs.db
```

### packages.yml

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0"]
  - package: elementary-data/elementary
    version: [">=0.20.0"]
  - package: calogica/dbt_expectations
    version: [">=0.10.0"]
```

### docker-compose.yml — Scaffold Structure

```yaml
services:
  lightdash:
    image: lightdash/lightdash:latest
    platform: linux/arm64
    profiles: ["simple", "postgres", "lakehouse", "full"]
    ports:
      - "18000:3000"
    environment:
      - LIGHTDASH_SECRET_KEY=${LIGHTDASH_SECRET_KEY}
    restart: unless-stopped

  # postgres profile placeholder — Story 1.3 adds full service config
  postgres:
    image: postgres:latest
    platform: linux/arm64
    profiles: ["postgres", "full"]
    ports:
      - "${POSTGRES_PORT:-18040}:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    restart: unless-stopped
```

Key requirements:
- Docker Compose v2 syntax — no `version:` key (deprecated in v2)
- `platform: linux/arm64` on every service (NFR11 — ARM64-first)
- Service names `lowercase-hyphenated`
- Story 1.3 adds the complete port map for all 15 services

### Verified Package Versions (2026-03-25)

| Package | Version | Notes |
|---|---|---|
| dbt-core | 1.11.7 | |
| dbt-duckdb | ≥1.8.x | Requires DuckDB 1.1.x |
| dbt-postgres | 1.10.0 | |
| dbt-trino | 1.10.1 | |
| Elementary | 0.20.0+ | |
| dlt | latest | Via PyPI |

Docker images use `latest` tags intentionally — documented as anti-pattern for production (NFR note in architecture).

### Port Allocation Reference (for docker-compose.yml stubs)

Full port map (Story 1.3 implements all of these, but good to know for scaffold):

| Service | Port | Profile |
|---|---|---|
| Lightdash | 18000 | all |
| Evidence | 18010 | all |
| dbt docs | 18020 | all |
| Elementary | 18030 | all |
| Postgres | 18040 | postgres |
| MinIO console | 18050 | lakehouse |
| MinIO API | 18060 | lakehouse |
| Trino | 18070 | lakehouse |
| Airflow | 18080 | full |
| OpenMetadata | 18090 | full |
| Prometheus | 18100 | full |
| Grafana | 18110 | full |
| Keycloak | 18120 | full |
| Superset | 18130 | full |
| MCP Server | 18140 | full |

[Source: architecture.md#Port Allocation Map]

### Project Structure to Create

```
local-data-platform/          ← REPO ROOT = dbt project root
├── README.md                 stub only
├── .env.example              all required env vars with placeholders
├── .gitignore                excludes .env, target/, logs/, __pycache__/
├── Makefile                  make help must work; other targets are stubs
├── requirements.txt          dlt, faker, pandas
├── dbt_project.yml           project root, schema config, layer tags
├── packages.yml              elementary, dbt-expectations, dbt_utils
├── profiles.yml              env-var driven: DuckDB + Postgres + Trino
├── docker-compose.yml        profile scaffold; full ports in Story 1.3
│
├── models/
│   ├── bronze/
│   │   ├── sources.yml       EMPTY placeholder — NO SQL models ever
│   │   └── .gitkeep
│   ├── silver/
│   │   └── .gitkeep
│   ├── gold/
│   │   ├── facts/
│   │   │   └── .gitkeep
│   │   ├── dimensions/
│   │   │   └── .gitkeep
│   │   └── marts/
│   │       └── .gitkeep
│   ├── quarantine/
│   │   └── .gitkeep
│   └── metrics/
│       └── .gitkeep
│
├── macros/
│   └── adapters/
│       └── .gitkeep
├── tests/
│   └── .gitkeep
├── seeds/
│   └── .gitkeep              Jaffle Shop seeds added in Epic 2
├── analyses/
│   └── .gitkeep
│
├── ingest/
│   └── .gitkeep              dlt scripts + Faker generator added in Epic 2
├── data/
│   └── .gitkeep
├── docker/
│   └── .gitkeep
├── docs/
│   └── .gitkeep
├── terraform/
│   └── .gitkeep
│
└── .github/
    └── workflows/
        └── ci.yml            maintainer CI: dbt compile + sqlfluff + yamllint
```

### Story Scope Boundaries

**IN SCOPE (this story):**
- Full directory skeleton
- `dbt_project.yml` — schema config, model paths, layer tags
- `profiles.yml` — env-var connection setup for DuckDB, Postgres, Trino
- `packages.yml` — dependency declarations
- `Makefile` — `make help` working; all other targets are stubs
- `.env.example` — all required env vars documented
- `.gitignore`
- `docker-compose.yml` scaffold — profile blocks, ARM64, at least one service per profile
- `requirements.txt`
- `README.md` stub
- `.github/workflows/ci.yml` maintainer CI skeleton

**OUT OF SCOPE (separate stories):**
- Working `make start`/`make stop` that actually boots services → Story 1.2
- Full port allocation map across all 15 services → Story 1.3
- Any dlt ingestion scripts → Epic 2
- Any Silver/Gold dbt model files → Epic 2
- Full README content (hardware, quick-start, WSL2 notes) → Story 2.14
- Jaffle Shop seed data → Epic 2

### FR/NFR Coverage

| Requirement | Implementation |
|---|---|
| FR4 | `make help` lists all targets — works immediately after scaffold |
| FR1, FR2, FR3 | Makefile stubs exist; `.env` + `COMPOSE_PROFILES` mechanism wired |
| FR49 | Port stubs in `docker-compose.yml`; full port map in Story 1.3 |
| NFR6 | `.gitignore` excludes all `.env` variants |
| NFR7 | `.env.example` ships with placeholder values |
| NFR10 | `docker compose` v2 syntax (no `version:` key) |
| NFR19 | Docker Compose profile blocks isolate services per profile |
| NFR20 | All profile config in `.env` and `docker-compose.yml` only |
| NFR21 | `make help` auto-documentation via `##` comments |

### Anti-Patterns to Avoid

- ❌ Any `.sql` file under `models/bronze/` — Bronze has zero dbt materializations
- ❌ Adding a `bronze:` schema block in `dbt_project.yml` — Bronze is a source, not a model folder
- ❌ Hardcoding credentials in `profiles.yml` or any config file
- ❌ Using `docker-compose` v1 syntax (must be `docker compose` v2)
- ❌ Makefile targets without `##` comment — breaks `make help`
- ❌ Makefile targets using `snake_case` or `camelCase` — must be `kebab-case`
- ❌ Env vars without service prefix (`DB_HOST` → should be `POSTGRES_HOST`)
- ❌ Placing `dbt_project.yml` in a subdirectory — must be at repo root

### References

- [Source: epics.md#Story 1.1 Acceptance Criteria]
- [Source: architecture.md#Data Architecture — Repository Structure, Schema Naming, Bronze Layer Ownership]
- [Source: architecture.md#Implementation Patterns — Naming Patterns, Structure Patterns, Format Patterns]
- [Source: architecture.md#Project Structure & Boundaries]
- [Source: architecture.md#Starter Template Evaluation — Initialization Sequence, Verified Package Versions]
- [Source: prd.md#Implementation Considerations]
- [Source: prd.md#Non-Functional Requirements]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- All 12 tasks completed. Full directory skeleton created with `.gitkeep` in every tracked directory.
- `dbt_project.yml`: Silver/gold/quarantine/metrics schema+materialization config; no `bronze` block (Bronze is a source).
- `profiles.yml`: Fully env-var driven — DuckDB (simple), Postgres, Trino (lakehouse) targets; active target via `COMPOSE_PROFILES`.
- `Makefile`: `make help` verified working with exit code 0; all 6 targets with `##` comments in `kebab-case`.
- `docker-compose.yml`: Docker Compose v2 syntax; `platform: linux/arm64` on all services; one service per profile (simple/postgres/lakehouse/full).
- `.env.example`: All required vars with inline comments; zero real credentials.
- `.gitignore`: Excludes `.env`/`.env.*` except `.env.example`; dbt artifacts; Python caches; OS files.
- `.github/workflows/ci.yml`: Maintainer CI with `dbt compile`, `sqlfluff`, `yamllint` on push/PR to main.
- `models/bronze/` contains only `sources.yml` + `.gitkeep` — zero `.sql` files (enforced by verification).
- ✅ Resolved review finding [Patch]: Added `full` dbt output to `profiles.yml` (Trino/iceberg, same as `lakehouse`) — `COMPOSE_PROFILES=full` now maps to a valid dbt target.
- ✅ Resolved review finding [Patch]: Removed `continue-on-error: true` from `sqlfluff lint` and `yamllint` CI steps — lint failures now correctly fail the CI job.

### File List

- `.env.example`
- `.gitignore`
- `.github/workflows/ci.yml`
- `Makefile`
- `README.md`
- `dbt_project.yml`
- `docker-compose.yml`
- `packages.yml`
- `profiles.yml`
- `requirements.txt`
- `models/bronze/.gitkeep`
- `models/bronze/sources.yml`
- `models/silver/.gitkeep`
- `models/gold/facts/.gitkeep`
- `models/gold/dimensions/.gitkeep`
- `models/gold/marts/.gitkeep`
- `models/quarantine/.gitkeep`
- `models/metrics/.gitkeep`
- `macros/adapters/.gitkeep`
- `tests/.gitkeep`
- `seeds/.gitkeep`
- `analyses/.gitkeep`
- `ingest/.gitkeep`
- `data/.gitkeep`
- `docker/.gitkeep`
- `terraform/.gitkeep`

## Change Log

- 2026-03-25: Story 1.1 implemented — full repository scaffold created (12 tasks, all ACs satisfied). Created directory skeleton, dbt_project.yml, profiles.yml, packages.yml, Makefile, .env.example, .gitignore, docker-compose.yml, requirements.txt, README.md stub, and .github/workflows/ci.yml. Status → review.
- 2026-03-25: Addressed code review findings — 2 items resolved. Added `full` dbt target to profiles.yml; removed continue-on-error from CI lint steps. Status → review.
