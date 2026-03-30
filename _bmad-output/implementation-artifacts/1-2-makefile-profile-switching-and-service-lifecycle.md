# Story 1.2: Makefile Profile Switching and Service Lifecycle

Status: done

## Story

As a data engineer,
I want to start and stop profile services using a single Makefile command and switch profiles via a single `.env` variable,
So that I can move between deployment profiles without modifying any pipeline code.

## Acceptance Criteria

1. **Given** `COMPOSE_PROFILES=simple` is set in `.env`, **When** I run `make start`, **Then** all `simple` profile services start successfully using Docker Compose v2 syntax, **And** no services from other profiles (`postgres`, `lakehouse`, `full`) are started.

2. **Given** services are running, **When** I run `make stop`, **Then** all running services stop cleanly with exit code 0.

3. **Given** I change `COMPOSE_PROFILES` in `.env` from `simple` to `postgres`, **When** I run `make start`, **Then** the `postgres` profile services start without any changes to dbt models, ingestion scripts, or `schema.yml`, **And** `make stop` cleanly stops the `postgres` profile services.

4. **Given** a fresh Docker state (`docker compose down -v` completed), **When** I run `make start` for any profile, **Then** services start cleanly without manual intervention.

## Tasks / Subtasks

- [x] Task 1: Implement `start` Makefile target (AC: 1, 3, 4)
  - [x] Replace the stub `start` target with `docker compose up -d`
  - [x] Add guard: if `.env` is missing, print helpful error and exit 1 (`cp .env.example .env`)
  - [x] Print the active `COMPOSE_PROFILES` value before starting (read from `.env` via `grep`)
  - [x] Verify `@` prefix suppresses `docker compose` command echo (keep output clean)

- [x] Task 2: Implement `stop` Makefile target (AC: 2)
  - [x] Replace stub with `docker compose down`
  - [x] Confirm exit code 0 when no services are running (idempotent stop)

- [x] Task 3: Verify `docker-compose.yml` profile isolation (AC: 1, 3)
  - [x] Confirm `lightdash` service has `profiles: ["simple", "postgres", "lakehouse", "full"]`
  - [x] Confirm `postgres` service has `profiles: ["postgres", "full"]`
  - [x] Verify `COMPOSE_PROFILES=simple` starts only `lightdash` + `lightdash-db` (not `postgres` data warehouse)
  - [x] Verify `COMPOSE_PROFILES=postgres` starts `lightdash` + `lightdash-db` + `postgres` (not lakehouse/full services)
  - [x] VERIFY: `docker compose config --profiles` lists all declared profiles correctly

- [x] Task 4: Verify `.env` → Docker Compose → `COMPOSE_PROFILES` flow (AC: 1, 3, 4)
  - [x] Confirmed Docker Compose v2 auto-reads `.env` from CWD — no `--env-file` flag required
  - [x] Confirmed `COMPOSE_PROFILES` value in `.env` is the sole profile selector (NFR20)
  - [x] Confirmed dbt `profiles.yml` target also resolves via `COMPOSE_PROFILES` (no code changes when switching)

- [x] Task 5: Final verification — all 4 ACs (AC: 1, 2, 3, 4)
  - [x] AC1: `COMPOSE_PROFILES=simple` in `.env` → `make start` → only `lightdash` + `lightdash-db` running ✅
  - [x] AC2: `make stop` → all containers stopped, exit code 0 ✅
  - [x] AC3: Edit `.env` to `COMPOSE_PROFILES=postgres` → `make start` → `lightdash` + `lightdash-db` + `postgres` running, zero file changes outside `.env` ✅
  - [x] AC4: `docker compose down -v` → `make start` → services start without errors or manual steps ✅

### Review Findings

- [x] [Review][Patch] `start` and `stop` leak raw Docker commands instead of keeping output clean [`Makefile:9`]

## Dev Notes

### Critical Architecture Constraints

**Docker Compose v2 Syntax — Non-Negotiable**
- Use `docker compose` (v2, space), NOT `docker-compose` (v1, hyphen) — NFR10
- Docker Compose v2 automatically reads `.env` from the working directory
- `COMPOSE_PROFILES` in `.env` is natively understood by Docker Compose — no extra flags needed
- [Source: architecture.md#Integration, NFR10]

**`COMPOSE_PROFILES` as Single Profile Selector**
- `COMPOSE_PROFILES` is the ONE variable that controls both which Docker containers start AND which dbt adapter is active (`profiles.yml` target)
- Changing `COMPOSE_PROFILES` in `.env` is the only required action to switch profiles
- dbt models, ingestion scripts, and `schema.yml` must not contain profile-specific logic — NFR20
- [Source: architecture.md#Technical Constraints]

**Makefile Target Requirements**
- `kebab-case` names — `make start`, `make stop` (already correct)
- Every target MUST have `##` comment on the same line for `make help` auto-documentation — NFR21
- Use `@` prefix to suppress command echo for cleaner UX
- [Source: architecture.md#Naming Patterns — Makefile Target Naming]

### `make start` Implementation

```makefile
start: ## Start all services for the active COMPOSE_PROFILES
	@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)
	@echo "▶  Starting profile: $$(grep -E '^COMPOSE_PROFILES=' .env | cut -d= -f2)"
	docker compose up -d
```

Key points:
- `docker compose up -d` detached mode — returns immediately, services run in background
- `test -f .env` guard prevents confusing Docker Compose errors when `.env` is missing
- `grep` reads `COMPOSE_PROFILES` directly from `.env` for the display line (does not rely on shell env export)
- Docker Compose v2 reads `.env` automatically — `--env-file .env` is NOT needed (and would cause precedence confusion if the user has shell exports)

### `make stop` Implementation

```makefile
stop: ## Stop all running services
	docker compose down
```

Key points:
- `docker compose down` stops AND removes containers + networks (correct for this context)
- Does NOT remove volumes — data persists between stop/start cycles
- Idempotent: exits with code 0 even if no services are running
- To fully reset state (NFR15 clean cold-start test): `docker compose down -v` (removes volumes too — learner-facing command, not a Makefile target)

### Docker Compose Profile Mechanics

```yaml
# How Docker Compose profile assignment works:
services:
  lightdash:
    profiles: ["simple", "postgres", "lakehouse", "full"]  # starts on all profiles
  postgres:
    profiles: ["postgres", "full"]                          # postgres and full only
```

When `COMPOSE_PROFILES=simple`:
- `lightdash` starts (matches `simple`)
- `postgres` container does NOT start (not in `simple` profile list)

When `COMPOSE_PROFILES=postgres`:
- `lightdash` starts (matches `postgres`)
- `postgres` container starts (matches `postgres`)

This is native Docker Compose v2 behaviour — no custom logic required.

### What `docker-compose.yml` Contains After Story 1.1

Story 1.1 created a scaffold with two services:
1. `lightdash` — profiles: all, port 18000
2. `postgres` — profiles: postgres/full, port 18040

The full 15-service port map is implemented in Story 1.3. This story only needs these two services to prove the profile isolation mechanism works.

Do NOT add new services to `docker-compose.yml` in this story — that is Story 1.3's scope.

### `.env` Auto-Loading: Docker Compose vs Shell

Docker Compose v2 loads `.env` automatically for **variable substitution** in `docker-compose.yml` (e.g. `${COMPOSE_PROFILES}`, `${POSTGRES_PORT:-18040}`). This is separate from the Makefile shell environment.

The Makefile recipe shell does NOT automatically see `.env` variables. To display the active profile in `make start`, read directly from the file with `grep`:
```bash
$$(grep -E '^COMPOSE_PROFILES=' .env | cut -d= -f2)
```

Do NOT use `-include .env` + `export` in the Makefile — this would make all `.env` secrets available as Make variables, which is a security anti-pattern.

### Verified docker-compose.yml Lightdash Minimum Config

For Lightdash to start on the `simple` profile, it requires `LIGHTDASH_SECRET_KEY` (already in `.env.example`). The container will start with SQLite as its internal metadata store by default — no Postgres dependency for the `simple` profile.

### Story Scope Boundaries

**IN SCOPE (this story):**
- `make start` target — invokes `docker compose up -d` with `.env` guard
- `make stop` target — invokes `docker compose down`
- Verification that profile isolation works with the Story 1.1 scaffold
- Confirming `COMPOSE_PROFILES` flows from `.env` → Docker Compose → dbt profiles.yml

**OUT OF SCOPE:**
- Adding new services to `docker-compose.yml` → Story 1.3
- Full 15-service port allocation → Story 1.3
- `docker/init/` SQL scripts for schema creation → Story 1.3 (Postgres init) or later epics
- `make run-pipeline` implementation → Story 2.12
- `make open-docs` implementation → Story 2.12
- `.gitattributes` for WSL2 line endings → Story 2.14

### FR/NFR Coverage

| Requirement | Implementation |
|---|---|
| FR1 | `make start` starts complete profile environment |
| FR2 | `make stop` stops all services |
| FR3 | `COMPOSE_PROFILES` in `.env` switches profiles without code changes |
| NFR10 | `docker compose` v2 syntax throughout |
| NFR15 | Clean cold-start: `docker compose down -v` + `make start` |
| NFR19 | Each profile independently startable |
| NFR20 | Profile config isolated to `.env` — no dbt/ingestion code changes on switch |

### Previous Story Context (1.1)

The following files already exist from Story 1.1 and MUST NOT be regenerated:
- `Makefile` — update ONLY the `start` and `stop` target bodies; keep all other targets intact
- `docker-compose.yml` — verify only; do not add/remove services or change ports
- `.env.example` — read-only reference; do not modify
- `profiles.yml` — already has `simple`, `postgres`, `lakehouse`, `full` targets

Story 1.1 completion notes confirm:
- `make help` verified working with exit code 0
- All 6 targets present with `##` comments
- `docker-compose.yml` has Docker Compose v2 syntax, `platform: linux/arm64`, one service per profile

### Anti-Patterns to Avoid

- ❌ `docker-compose up` — must be `docker compose up` (v2 syntax)
- ❌ `--env-file .env` flag — Docker Compose v2 reads `.env` automatically; using `--env-file` can cause variable precedence confusion
- ❌ `-include .env` + `export` in Makefile — exposes secrets as Make variables
- ❌ Hardcoding profile names (`simple`, `postgres`) in Makefile — the profile is determined by `.env` alone
- ❌ `docker compose stop` — leaves zombie containers; use `docker compose down` for clean teardown
- ❌ Adding services to `docker-compose.yml` — Story 1.3 scope
- ❌ Modifying `start`/`stop` target names or `##` comment format — breaks `make help`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Lightdash ARM64: `lightdash/lightdash:latest` has no `linux/arm64` manifest. Fixed: `platform: linux/amd64` (Rosetta 2 emulation on Apple Silicon — NFR11 known exception).
- Lightdash env var: container requires `LIGHTDASH_SECRET`, not `LIGHTDASH_SECRET_KEY`. Renamed throughout.
- Lightdash requires Postgres metadata DB: discovered Lightdash cannot run without a Postgres instance even on the `simple` (DuckDB) profile. Added `lightdash-db` service (all profiles) as Lightdash's internal application database — separate from the dbt data warehouse.

### Completion Notes List

- `make start` implemented: `.env` guard + profile display + `docker compose up -d`. Verified with `simple` and `postgres` profiles.
- `make stop` implemented: `docker compose down`. Verified exit code 0 including idempotent stop.
- `docker-compose.yml`: Added `lightdash-db` (postgres, all profiles) as Lightdash's required internal metadata store; wired `lightdash` to it via `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`/`PGDATABASE` env vars and `depends_on`.
- `lightdash/lightdash:latest` changed to `platform: linux/amd64` — no ARM64 manifest available; runs under Rosetta 2 on Apple Silicon (documented as NFR11 known exception).
- Renamed `LIGHTDASH_SECRET_KEY` → `LIGHTDASH_SECRET` in `.env.example`, `docker-compose.yml` (Lightdash's actual required env var name).
- Added `LIGHTDASH_DB_PASSWORD` to `.env.example` for the `lightdash-db` metadata Postgres.
- All 4 ACs verified by live Docker execution: profile isolation confirmed, clean cold-start confirmed, no code changes required to switch profiles.

### File List

- `Makefile`
- `docker-compose.yml`
- `.env.example`

## Change Log

- 2026-03-25: Story 1.2 implemented — `make start` and `make stop` wired to Docker Compose v2; profile isolation verified live for `simple` and `postgres` profiles; added `lightdash-db` service; corrected `LIGHTDASH_SECRET` env var name; documented Lightdash ARM64 exception. All 4 ACs satisfied. Status → review.
- 2026-03-25: Addressed code review findings — 1 item resolved. Added `@` prefix to `docker compose up -d` and `docker compose down` to suppress raw command echo. Status → review.
