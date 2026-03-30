# Story 1.3: Port Allocation and Docker Compose Structure

Status: done

## Story

As a data engineer,
I want all services assigned to documented, non-conflicting ports from a high base,
So that the template does not collide with other local services and I can find any service endpoint quickly.

## Acceptance Criteria

1. **Given** the `docker-compose.yml` is implemented, **When** I inspect all service port declarations, **Then** all ports use the 18000+ base with increments of 10, matching the port map: Lightdash=18000, Evidence=18010, dbt docs=18020, Elementary=18030, Postgres=18040, MinIO console=18050, MinIO API=18060, Trino=18070, Airflow=18080, OpenMetadata=18090, Prometheus=18100, Grafana=18110, Keycloak=18120, Superset=18130, MCP Server=18140, **And** no two services share the same host port.

2. **Given** the README exists, **When** I search for the port allocation section, **Then** a complete port map table is present matching the `docker-compose.yml` declarations.

3. **Given** I run `make help`, **When** I read the output, **Then** resource requirements per profile (RAM) are documented alongside the relevant targets.

4. **Given** the `simple` profile is running, **When** I follow the connection string documented in the README, **Then** I can connect a standard SQL client (e.g. DuckDB CLI, DataGrip, or TablePlus) to the running DuckDB instance and query the `gold` schema directly — satisfying FR27.

## Tasks / Subtasks

- [x] Task 1: Complete `docker-compose.yml` — add all missing services with correct port allocations (AC: 1)
  - [x] Add `evidence` service (all profiles) — host port 18010 → container port 3000
  - [x] Add `dbt-docs` stub (all profiles) — host port 18020 → container port 8080; add comment: "Story 2.13 completes dbt docs serving config"
  - [x] Add `elementary` stub (all profiles) — host port 18030 → container port 8080; add comment: "Story 2.9 completes Elementary dashboard config"
  - [x] Verify `postgres` service already has host port 18040 (from Story 1.1) — no change needed
  - [x] Verify `minio` service already has host ports 18050 (console) + 18060 (API) — no change needed
  - [x] Add `trino` stub (lakehouse, full profiles) — host port 18070 → container port 8080
  - [x] Verify `airflow` stub already has host port 18080 — no change needed (Story 5.1 completes Airflow)
  - [x] Add `openmetadata` stub (full profile) — host port 18090 → container port 8585; add comment: "Story 4.3 completes OpenMetadata config"
  - [x] Add `prometheus` stub (full profile) — host port 18100 → container port 9090
  - [x] Add `grafana` stub (full profile) — host port 18110 → container port 3000
  - [x] Add `keycloak` stub (full profile) — host port 18120 → container port 8080
  - [x] Add `superset` stub (full profile) — host port 18130 → container port 8088; add comment: "Story 5.4 completes Superset config"
  - [x] Add `mcp-server` stub (full profile) — host port 18140 → container port 8000; add comment: "Story 5.5 completes MCP Server config"
  - [x] VERIFY: `docker compose config` parses without error (validates YAML and variable interpolation)
  - [x] VERIFY: No two services share the same host port number

- [x] Task 2: Add port map table to `README.md` (AC: 2)
  - [x] Add `## Port Allocation` section after `## Hardware Requirements`
  - [x] Include the complete 15-service table with Service, Host Port, Profile, and Status columns
  - [x] Add DuckDB connection note: file-based, no port (see FR27 connection section)
  - [x] VERIFY: Port numbers in README exactly match `docker-compose.yml` port declarations

- [x] Task 3: Add resource requirements to `Makefile` help output (AC: 3)
  - [x] Update `start` target `##` comment to include RAM note: e.g. `## Start all services for the active COMPOSE_PROFILES`
  - [x] Add inline comment block above `start` target documenting RAM per profile
  - [x] Alternatively: add a `profiles` Makefile target with `##` comment listing RAM requirements per profile
  - [x] VERIFY: `make help` output references RAM requirements so user can read them without opening Makefile

- [x] Task 4: Document DuckDB SQL client connection in `README.md` (AC: 4)
  - [x] Add `## Connecting to DuckDB (simple profile)` subsection in Port Allocation or Quick Start section
  - [x] Document DuckDB CLI: `duckdb dev.duckdb` → `SELECT * FROM gold.orders LIMIT 10;`
  - [x] Document DataGrip/TablePlus: open file `dev.duckdb` at repo root (DuckDB JDBC driver required)
  - [x] Note: `dev.duckdb` is created by `dbt run` — connect after running the pipeline (Epic 2)
  - [x] Note: `gold` schema is populated after `dbt run` completes
  - [x] VERIFY: Connection instructions reference the correct `DBT_DUCKDB_PATH` default value (`dev.duckdb`)

- [x] Task 5: Final verification — all 4 ACs (AC: 1, 2, 3, 4)
  - [x] AC1: `docker compose config` parses cleanly; count 15 distinct host ports all in 18000-18140 range; verify no duplicates
  - [x] AC2: `README.md` contains port map table with all 15 services
  - [x] AC3: `make help` output shows RAM requirement guidance alongside profile targets
  - [x] AC4: README documents DuckDB file path and how to query `gold` schema

### Review Findings

- [x] [Review][Patch] `make help` still omits the actual RAM requirements promised by AC3 [`Makefile:23`]

## Dev Notes

### Critical: Current `docker-compose.yml` State (Post Stories 1.1 + 1.2)

The following services ALREADY EXIST in `docker-compose.yml` — do NOT re-create or overwrite:

| Service | Profiles | Host Port | Container Port | Notes |
|---|---|---|---|---|
| `lightdash-db` | all | none exposed | 5432 | Lightdash internal metadata DB — NOT the data warehouse |
| `lightdash` | all | 18000 | 3000 | `platform: linux/amd64` — confirmed ARM64 exception |
| `postgres` | postgres, full | 18040 | 5432 | Data warehouse; Story 1.3: verify only |
| `minio` | lakehouse, full | 18050 (console), 18060 (API) | 9001, 9000 | Object storage |
| `airflow` | full | 18080 | 8080 | Stub only — Story 5.1 completes Airflow setup |

**Critical lessons from Story 1.2 to carry forward:**
- `lightdash` must remain `platform: linux/amd64` (no ARM64 manifest — NFR11 documented exception)
- `lightdash-db` must NOT have a host port exposed (internal only — avoids conflict with `postgres` on 5432)
- `LIGHTDASH_SECRET` is the correct env var name (NOT `LIGHTDASH_SECRET_KEY` — verified live)
- Docker Compose v2 syntax throughout: `docker compose` not `docker-compose`, no `version:` key

### Service Configuration for New Stubs

Add each service in order of their port number. All new services are **stubs** — minimal config for port reservation. Their full configuration is completed in dedicated implementation stories.

#### `evidence` — All Profiles, Port 18010

```yaml
  # Evidence — analytical reporting (all profiles)
  # Story 2.11 completes Evidence project config and volume mounts
  evidence:
    image: ghcr.io/evidence-dev/evidence:latest
    platform: linux/arm64
    profiles: ["simple", "postgres", "lakehouse", "full"]
    ports:
      - "18010:3000"
    restart: unless-stopped
```

**ARM64 status:** Evidence is a Node.js app — ARM64 images available. Verify at runtime; apply `platform: linux/amd64` only if no ARM64 manifest found (same pattern as lightdash).

**Note:** Evidence requires project files mounted at `/evidence` and `EVIDENCE_SOURCE=duckdb` configuration. Story 2.11 adds volume mounts and environment config. For Story 1.3, the stub is sufficient for port reservation.

#### `dbt-docs` — All Profiles, Port 18020

```yaml
  # dbt docs — generated documentation server (all profiles)
  # Served via 'dbt docs serve --port 18020' or 'make open-docs'
  # Story 2.13 completes dbt documentation and serving setup
  dbt-docs:
    image: python:3.11-slim
    platform: linux/arm64
    profiles: ["simple", "postgres", "lakehouse", "full"]
    ports:
      - "18020:8080"
    command: python -m http.server 8080 -d /app
    restart: unless-stopped
```

**Alternative approach:** `dbt docs serve` is a CLI command typically run on the host (not in Docker). If the team prefers Makefile-driven serving, omit this service and instead use:
```makefile
serve-docs: ## Serve dbt docs on http://localhost:18020
	dbt docs generate && dbt docs serve --port 18020
```

The AC requires all 15 ports documented — if using Makefile, still add this service to the port map table in README with a "CLI only" note.

#### `elementary` — All Profiles, Port 18030

```yaml
  # Elementary — data observability dashboard (all profiles)
  # Story 2.9 completes Elementary install and edr report config
  elementary:
    image: python:3.11-slim
    platform: linux/arm64
    profiles: ["simple", "postgres", "lakehouse", "full"]
    ports:
      - "18030:8080"
    command: python -m http.server 8080 -d /app
    restart: unless-stopped
```

**Note:** Elementary runs via `edr report` CLI locally. Port 18030 is reserved for when it serves locally. Story 2.9 implements Elementary fully. Same Docker approach as dbt-docs stub.

#### `trino` — Lakehouse + Full Profiles, Port 18070

```yaml
  # Trino — distributed query engine (lakehouse, full profiles)
  # Story 4.1 completes Trino config with Iceberg catalog
  trino:
    image: trinodb/trino:latest
    platform: linux/arm64
    profiles: ["lakehouse", "full"]
    ports:
      - "18070:8080"
    restart: unless-stopped
```

**ARM64 status:** Trino official image (`trinodb/trino`) includes ARM64 support. No `linux/amd64` override needed.

**Internal port:** Trino's HTTP coordinator port is 8080 by default (configured in `etc/config.properties`).

#### `openmetadata` — Full Profile, Port 18090

```yaml
  # OpenMetadata — data catalog and lineage (full profile)
  # Story 4.3 completes OpenMetadata config; requires Elasticsearch + MySQL dependencies
  openmetadata:
    image: openmetadata/server:latest
    platform: linux/amd64
    profiles: ["full"]
    ports:
      - "18090:8585"
    restart: unless-stopped
```

**ARM64 status:** OpenMetadata server image does NOT have ARM64 support as of March 2026. Use `platform: linux/amd64` (Rosetta 2 on Apple Silicon — NFR11 known exception). Document this in code comment.

**Critical:** OpenMetadata in production requires Elasticsearch, MySQL, and Airflow as dependencies. Story 4.3 adds these. For Story 1.3, the stub is for port reservation only — do NOT start the `full` profile expecting OpenMetadata to work.

#### `prometheus` — Full Profile, Port 18100

```yaml
  # Prometheus — metrics collection (full profile)
  # Story 5.2 adds prometheus.yml config and scrape targets
  prometheus:
    image: prom/prometheus:latest
    platform: linux/arm64
    profiles: ["full"]
    ports:
      - "18100:9090"
    restart: unless-stopped
```

**ARM64 status:** `prom/prometheus` provides native ARM64 images. No override needed.

#### `grafana` — Full Profile, Port 18110

```yaml
  # Grafana — observability dashboards (full profile)
  # Story 5.2 adds Grafana datasource and dashboard provisioning
  grafana:
    image: grafana/grafana:latest
    platform: linux/arm64
    profiles: ["full"]
    ports:
      - "18110:3000"
    restart: unless-stopped
```

**ARM64 status:** `grafana/grafana` provides native ARM64 images.

**Internal port:** Grafana default HTTP port is 3000 (same as Lightdash and Evidence container ports — but different host ports so no conflict).

#### `keycloak` — Full Profile, Port 18120

```yaml
  # Keycloak — SSO and service authentication (full profile)
  # Story 5.3 completes Keycloak realm config and service integration
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    platform: linux/arm64
    profiles: ["full"]
    ports:
      - "18120:8080"
    environment:
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN:-admin}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD:-changeme}
    command: start-dev
    restart: unless-stopped
```

**ARM64 status:** Keycloak official image (`quay.io/keycloak/keycloak`) supports ARM64.

**`start-dev` mode:** Required for non-production local use (no TLS requirement). Story 5.3 may switch to production mode with proper TLS termination.

**.env.example additions needed:**
```bash
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=changeme
```

#### `superset` — Full Profile, Port 18130

```yaml
  # Superset — BI and data exploration (full profile)
  # Story 5.4 adds Redis + Celery config for full Superset functionality
  superset:
    image: apache/superset:latest
    platform: linux/amd64
    profiles: ["full"]
    ports:
      - "18130:8088"
    environment:
      SUPERSET_SECRET_KEY: ${SUPERSET_SECRET_KEY:-changeme-generate-a-random-string}
    restart: unless-stopped
```

**ARM64 status:** `apache/superset:latest` does NOT have reliable ARM64 support as of March 2026. Use `platform: linux/amd64` (Rosetta 2 on Apple Silicon — NFR11 known exception).

**.env.example additions needed:**
```bash
SUPERSET_SECRET_KEY=changeme-generate-a-random-string
```

#### `mcp-server` — Full Profile, Port 18140

```yaml
  # MCP Server — AI agent interface via MetricFlow (full profile)
  # Story 5.5 builds and configures the MCP Server implementation
  mcp-server:
    image: python:3.11-slim
    platform: linux/arm64
    profiles: ["full"]
    ports:
      - "18140:8000"
    command: echo "MCP Server not yet implemented — Story 5.5"
    restart: "no"
```

**Note:** The MCP Server is a custom implementation. Story 5.5 will replace the `python:3.11-slim` stub with the actual MCP server container. Use `restart: "no"` for the stub so it doesn't spam logs.

### `.env.example` — Required Additions

Add the following variables to `.env.example` (only add what doesn't already exist):

```bash
# Keycloak — SSO (full profile)
# Admin username for Keycloak master realm
KEYCLOAK_ADMIN=admin
# Admin password — replace with a strong password
KEYCLOAK_ADMIN_PASSWORD=changeme

# Superset — BI dashboard (full profile)
# Random secret key — generate with: openssl rand -hex 32
SUPERSET_SECRET_KEY=changeme-generate-a-random-string
```

Do NOT remove or modify existing variables in `.env.example`.

### ARM64 Summary — All Services

| Service | ARM64? | Notes |
|---|---|---|
| lightdash-db | ✅ native | postgres:latest has ARM64 |
| lightdash | ❌ `linux/amd64` | No ARM64 manifest (confirmed Story 1.2) |
| evidence | ✅ verify | Node.js — likely ARM64; confirm at first `make start` |
| dbt-docs | ✅ native | python:3.11-slim |
| elementary | ✅ native | python:3.11-slim |
| postgres | ✅ native | postgres:latest |
| minio | ✅ native | minio/minio:latest |
| trino | ✅ native | trinodb/trino:latest |
| airflow | ❓ verify | apache/airflow:latest — verify ARM64 support |
| openmetadata | ❌ `linux/amd64` | No ARM64 manifest as of 2026-03 |
| prometheus | ✅ native | prom/prometheus:latest |
| grafana | ✅ native | grafana/grafana:latest |
| keycloak | ✅ native | quay.io/keycloak/keycloak:latest |
| superset | ❌ `linux/amd64` | No reliable ARM64 as of 2026-03 |
| mcp-server | ✅ native | python:3.11-slim stub |

**If any image fails to pull on Apple Silicon:** Apply `platform: linux/amd64` and add a comment noting it as an NFR11 known exception.

### README Port Map Table Template

Add after `## Hardware Requirements`:

```markdown
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
```

### Makefile Resource Requirements

The AC says "resource requirements per profile (RAM) are documented alongside the relevant targets". Options:

**Option A — New `profiles` target (recommended):**
```makefile
profiles: ## Show available profiles and their hardware requirements
	@echo ""
	@echo "Available profiles (set COMPOSE_PROFILES in .env):"
	@echo ""
	@echo "  simple    — DuckDB + Lightdash + Evidence + dbt docs + Elementary"
	@echo "              Minimum RAM: 8 GB"
	@echo ""
	@echo "  postgres  — simple profile + Postgres data warehouse"
	@echo "              Minimum RAM: 8 GB"
	@echo ""
	@echo "  lakehouse — postgres profile + MinIO + Trino (Iceberg)"
	@echo "              Minimum RAM: 16 GB"
	@echo ""
	@echo "  full      — lakehouse profile + Airflow + OpenMetadata + Prometheus"
	@echo "              + Grafana + Keycloak + Superset + MCP Server"
	@echo "              Minimum RAM: 16 GB"
	@echo ""
```

Update `.PHONY` to include `profiles`.

**Option B — Update `start` target comment:**
```makefile
start: ## Start all services for the active COMPOSE_PROFILES (8GB RAM: simple/postgres; 16GB: lakehouse/full)
```

**Recommendation:** Use Option A (new `profiles` target) — it provides scannable output via `make profiles` and the `## Show available profiles...` text appears in `make help`. Option B keeps the `start` comment clean.

Add `profiles` to the `.PHONY` list in the Makefile.

### Story Scope Boundaries

**IN SCOPE (this story):**
- Add all 13 missing services as stubs to `docker-compose.yml` (complete port allocation)
- Add `.env.example` variables for Keycloak and Superset stubs
- Add port map table to `README.md`
- Add DuckDB connection instructions to `README.md`
- Add `profiles` Makefile target with RAM documentation
- Update `.PHONY` in Makefile

**OUT OF SCOPE (deferred to later stories):**
- Working Evidence project (Story 2.11)
- Working Elementary dashboard (Story 2.9)
- Working dbt docs server (Story 2.13)
- Trino Iceberg catalog configuration (Story 4.1)
- Postgres init SQL scripts / schema creation (Story 3.1)
- Full Airflow stack — scheduler, worker, metadata DB (Story 5.1)
- OpenMetadata dependencies — Elasticsearch, MySQL (Story 4.3)
- Prometheus scrape config (Story 5.2)
- Grafana dashboard provisioning (Story 5.2)
- Keycloak realm setup (Story 5.3)
- Superset Redis + Celery setup (Story 5.4)
- MCP Server implementation (Story 5.5)
- DuckDB pipeline data — `gold` schema only exists after `make run-pipeline` (Epic 2)
- Airflow webserver/scheduler split — Story 5.1 scope

**DO NOT modify these files beyond what's specified:**
- `profiles.yml` — already correct (simple/postgres/lakehouse/full targets)
- `dbt_project.yml` — no changes needed
- `packages.yml` — no changes needed
- `Makefile` targets other than `start` comment and adding `profiles`
- `models/` directory — no changes

### Anti-Patterns to Avoid

- ❌ `docker-compose` (v1 hyphen syntax) — must be `docker compose` (v2 space)
- ❌ `version: "3"` or any `version:` key in `docker-compose.yml` — deprecated in Compose v2
- ❌ Hardcoding passwords in `docker-compose.yml` — all secrets via `${VAR:-default}` substitution
- ❌ Exposing `lightdash-db` on a host port — it's an internal-only metadata DB, do NOT add port mapping
- ❌ Changing `lightdash` from `platform: linux/amd64` to `linux/arm64` — there is no ARM64 manifest
- ❌ Using `18000` for any service other than Lightdash — port assignments are fixed architecture decisions
- ❌ Adding full service configuration in this story — stubs only, complex config belongs in dedicated stories
- ❌ Modifying existing service definitions unless fixing an issue
- ❌ Breaking `make start` / `make stop` — these are already working, preserve them exactly
- ❌ Updating Makefile targets to use `snake_case` or `camelCase` — must be `kebab-case`
- ❌ Adding Makefile targets without `##` comment — required for `make help` auto-documentation

### FR/NFR Coverage

| Requirement | Implementation |
|---|---|
| FR27 | DuckDB connection instructions in README — SQL client can query `gold` schema via file path |
| FR49 | Complete 15-service port map in `docker-compose.yml` and README |
| NFR10 | Docker Compose v2 syntax throughout (no `version:` key, `docker compose` not `docker-compose`) |
| NFR11 | ARM64 exceptions documented: lightdash (`linux/amd64`), openmetadata (`linux/amd64`), superset (`linux/amd64`) |
| NFR15 | All new stubs use `restart: unless-stopped` enabling clean cold-start with `docker compose down -v` + `make start` |
| NFR18 | `simple`/`postgres` 8 GB; `lakehouse`/`full` 16 GB documented in `profiles` Makefile target and README |
| NFR19 | Each profile independently startable — new stubs assigned to correct profile arrays |
| NFR21 | New `profiles` Makefile target has `##` comment for `make help` auto-documentation |

### Previous Story Context (1.1 + 1.2)

Files modified in previous stories — PRESERVE as-is:
- `Makefile` — `start` and `stop` targets fully implemented; `help`, `install`, `run-pipeline`, `open-docs` already present
- `docker-compose.yml` — existing 5 services (lightdash-db, lightdash, postgres, minio, airflow) must not be modified except to verify they are correct
- `.env.example` — LIGHTDASH_SECRET (not LIGHTDASH_SECRET_KEY) and LIGHTDASH_DB_PASSWORD already present; only ADD new variables
- `README.md` — Hardware Requirements section already exists; ADD Port Allocation section after it

The `start` target uses `@` prefix for all commands (clean UX — reviewed and verified in Story 1.2). Maintain this pattern in any new Makefile recipes.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `dbt-docs` and `elementary` stubs: Story notes suggested `python -m http.server 8080 -d /app` but `/app` doesn't exist in `python:3.11-slim`. Used `tail -f /dev/null` instead — keeps container running, port mapped, no errors.
- `mcp-server`: Uses `restart: "no"` with `exit 0` command — exits cleanly once, does not restart, avoids log spam.
- Postgres port 18040 uses `${POSTGRES_PORT:-18040}:5432` variable syntax (from Story 1.1) — not matched by literal port grep; verified present manually.

### Completion Notes List

- `docker-compose.yml`: Added 10 new service stubs (evidence, dbt-docs, elementary, trino, openmetadata, prometheus, grafana, keycloak, superset, mcp-server). All 15 services now have host ports in the 18000–18140 range. `docker compose config` validates cleanly. No duplicate host ports.
- ARM64 exceptions documented: `lightdash` (existing, linux/amd64), `openmetadata` (linux/amd64, no ARM64 manifest), `superset` (linux/amd64, no reliable ARM64 manifest). All noted as NFR11 known exceptions in inline comments.
- `keycloak` uses `start-dev` mode and `quay.io/keycloak/keycloak:latest` with admin credentials via env vars.
- `mcp-server` stub uses `restart: "no"` — exits immediately to avoid log spam; Story 5.5 replaces it.
- `README.md`: Added `## Port Allocation` table (15 services), `## Connecting to DuckDB (simple profile)` with CLI and GUI client instructions. Port numbers in README match `docker-compose.yml` exactly.
- `Makefile`: Added `profiles` target with per-profile RAM requirements; added to `.PHONY`. `make help` now lists `profiles` target; `make profiles` displays full profile details with RAM.
- `.env.example`: Added `KEYCLOAK_ADMIN`, `KEYCLOAK_ADMIN_PASSWORD`, `SUPERSET_SECRET_KEY` with inline comments. No existing variables removed or modified.
- All 4 ACs verified: YAML valid, README has 15-row port table, `make help` lists `profiles`, README has DuckDB connection guide referencing `dev.duckdb`.

### File List

- `docker-compose.yml`
- `.env.example`
- `Makefile`
- `README.md`

## Change Log

- 2026-03-26: Story 1.3 created — port allocation and docker-compose structure.
- 2026-03-26: Story 1.3 implemented — all 15 services added to docker-compose.yml with correct 18000+ port allocation; README port map table and DuckDB connection guide added; Makefile `profiles` target with RAM requirements added; .env.example updated with Keycloak and Superset vars. All 4 ACs satisfied. Status → review.
- 2026-03-26: Addressed code review findings — 1 item resolved. Updated `profiles` target `##` comment to include RAM figures inline so `make help` directly shows "simple/postgres: 8 GB; lakehouse/full: 16 GB". Status → review.
