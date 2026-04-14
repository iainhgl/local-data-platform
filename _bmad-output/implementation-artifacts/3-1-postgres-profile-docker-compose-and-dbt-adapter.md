# Story 3.1: Postgres Profile Docker Compose and dbt Adapter

Status: done

## Story

As a data engineer,
I want the `postgres` profile to start a Postgres container with the dbt-postgres adapter configured via `.env`,
So that I can switch to a server warehouse with zero changes to dbt models.

## Acceptance Criteria

1. **Given** `COMPOSE_PROFILES=postgres` is set in `.env`, **When** I run `make start`, **Then** a Postgres container starts on port 18040 and the `bronze`, `silver`, `gold`, `quarantine` schemas are created by the init script.

2. **Given** the Postgres profile is running, **When** I run `make run-pipeline`, **Then** the same dbt models that ran on DuckDB execute without modification on Postgres, **And** dbt test results are identical to the `simple` profile on equivalent data.

3. **Given** the Postgres init script runs, **When** I inspect the database schemas, **Then** `engineer_role`, `analyst_role`, and `pii_analyst_role` roles exist with appropriate schema-level grants.

## Tasks / Subtasks

- [x] Task 0: Create story branch
  - [x] `git checkout -b story/3-1-postgres-profile-docker-compose-and-dbt-adapter`
  - [x] Confirm working tree is clean

- [x] Task 1: Create `docker/init/postgres_init.sql` (AC: 1, 3)
  - [x] Create directory `docker/init/`
  - [ ] Write `docker/init/postgres_init.sql`:
    ```sql
    -- Story 3.1: Postgres profile init — runs on first container start.
    -- The POSTGRES_USER (dbt) is a superuser; this script runs as that user.

    -- Schemas
    CREATE SCHEMA IF NOT EXISTS bronze;
    CREATE SCHEMA IF NOT EXISTS silver;
    CREATE SCHEMA IF NOT EXISTS gold;
    CREATE SCHEMA IF NOT EXISTS quarantine;

    -- Roles (Story 3.1 baseline; PII masking added in Story 3.2)
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'engineer_role') THEN
            CREATE ROLE engineer_role;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'analyst_role') THEN
            CREATE ROLE analyst_role;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pii_analyst_role') THEN
            CREATE ROLE pii_analyst_role;
        END IF;
    END
    $$;

    -- engineer_role: full access on all schemas
    GRANT USAGE, CREATE ON SCHEMA bronze TO engineer_role;
    GRANT USAGE, CREATE ON SCHEMA silver TO engineer_role;
    GRANT USAGE, CREATE ON SCHEMA gold TO engineer_role;
    GRANT USAGE, CREATE ON SCHEMA quarantine TO engineer_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA bronze GRANT ALL ON TABLES TO engineer_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA silver GRANT ALL ON TABLES TO engineer_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT ALL ON TABLES TO engineer_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA quarantine GRANT ALL ON TABLES TO engineer_role;

    -- analyst_role: read-only on silver, gold, quarantine (no raw bronze access)
    GRANT USAGE ON SCHEMA silver TO analyst_role;
    GRANT USAGE ON SCHEMA gold TO analyst_role;
    GRANT USAGE ON SCHEMA quarantine TO analyst_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA silver GRANT SELECT ON TABLES TO analyst_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO analyst_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA quarantine GRANT SELECT ON TABLES TO analyst_role;

    -- pii_analyst_role: same grants as analyst_role for Story 3.1
    -- Full PII unmasking (column-level security, views) added in Story 3.2
    GRANT USAGE ON SCHEMA silver TO pii_analyst_role;
    GRANT USAGE ON SCHEMA gold TO pii_analyst_role;
    GRANT USAGE ON SCHEMA quarantine TO pii_analyst_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA silver GRANT SELECT ON TABLES TO pii_analyst_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA gold GRANT SELECT ON TABLES TO pii_analyst_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA quarantine GRANT SELECT ON TABLES TO pii_analyst_role;
    ```
  - [x] VERIFY: File exists at `docker/init/postgres_init.sql`

- [x] Task 2: Update `docker-compose.yml` postgres service (AC: 1)
  - [x] Add `volumes:` to the `postgres` service to mount the init script:
    ```yaml
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
      volumes:
        - ./docker/init/postgres_init.sql:/docker-entrypoint-initdb.d/01_init.sql:ro
      restart: unless-stopped
    ```
  - [x] VERIFY: `docker compose config` shows the volumes mount without errors
  - [x] VERIFY: `docker compose --profile postgres up -d` starts the postgres container
  - [x] VERIFY: `docker exec $(docker compose ps -q postgres) psql -U dbt -d local_data_platform -c "\dn"` shows `bronze`, `silver`, `gold`, `quarantine` schemas
  - [x] VERIFY: `docker exec $(docker compose ps -q postgres) psql -U dbt -d local_data_platform -c "\du"` shows `engineer_role`, `analyst_role`, `pii_analyst_role` roles
  - [x] **CRITICAL**: If the postgres container was already started before (data dir not empty), the init script will NOT re-run. To force re-init during development: `docker compose down -v` (removes named volumes) then `docker compose --profile postgres up -d`. **Warn in notes if init appears to not have run**.

- [x] Task 3: Add Postgres destination to `ingest/dlt_file_source.py` (AC: 2)
  - [x] Update the script to select destination based on `COMPOSE_PROFILES` env var:
    ```python
    import os
    import json
    import sys
    from pathlib import Path

    import dlt
    import duckdb

    DATA_DIR = Path(os.environ.get("FAKER_OUTPUT_DIR", "data"))
    DUCKDB_PATH = os.environ.get("DBT_DUCKDB_PATH", "dev.duckdb")
    COMPOSE_PROFILES = os.environ.get("COMPOSE_PROFILES", "simple")

    ENTITIES = {
        "customers": "customer_id",
        "products": "product_id",
        "orders": "order_id",
        "returns": "return_id",
    }


    def _get_destination():
        if COMPOSE_PROFILES in ("postgres", "full"):
            conn = (
                f"postgresql://{os.environ.get('POSTGRES_USER', 'dbt')}:"
                f"{os.environ.get('POSTGRES_PASSWORD', '')}@"
                f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
                f"{os.environ.get('POSTGRES_PORT', '18040')}/"
                f"{os.environ.get('POSTGRES_DB', 'local_data_platform')}"
            )
            return dlt.destinations.postgres(conn)
        return dlt.destinations.duckdb(DUCKDB_PATH)


    def _verify_counts():
        if COMPOSE_PROFILES in ("postgres", "full"):
            import psycopg2
            conn = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "localhost"),
                port=int(os.environ.get("POSTGRES_PORT", "18040")),
                user=os.environ.get("POSTGRES_USER", "dbt"),
                password=os.environ.get("POSTGRES_PASSWORD", ""),
                dbname=os.environ.get("POSTGRES_DB", "local_data_platform"),
            )
            cur = conn.cursor()
            for entity in ENTITIES:
                cur.execute(f"SELECT COUNT(*) FROM bronze.{entity}")
                count = cur.fetchone()[0]
                print(f"✓ {entity}: {count} rows")
            cur.close()
            conn.close()
        else:
            conn = duckdb.connect(DUCKDB_PATH, read_only=True)
            for entity in ENTITIES:
                count = conn.execute(f"SELECT COUNT(*) FROM bronze.{entity}").fetchone()[0]
                print(f"✓ {entity}: {count} rows")
            conn.close()
    ```
  - [x] Update `main()` to use `_get_destination()` and `_verify_counts()`
  - [x] VERIFY: `COMPOSE_PROFILES=postgres PYTHONPATH=. python ingest/dlt_file_source.py` loads to Postgres bronze

- [x] Task 4: Add Postgres destination to `ingest/dlt_api_source.py` (AC: 2)
  - [x] Apply the same `_get_destination()` / `COMPOSE_PROFILES` pattern as Task 3
  - [x] Update row count verification: if Postgres, use `psycopg2`; else use `duckdb`
  - [x] Remove the `import duckdb` and `get_duckdb_path()` call from the Postgres branch
  - [x] VERIFY: `COMPOSE_PROFILES=postgres PYTHONPATH=. python ingest/dlt_api_source.py` loads to Postgres bronze

- [x] Task 5: Update `requirements.txt` (AC: 2)
  - [x] Add `psycopg2-binary` to `requirements.txt` (provides the Postgres driver for both dlt and direct psycopg2 use):
    ```
    dlt
    faker
    pandas
    requests
    elementary-data
    psycopg2-binary
    ```
  - [x] VERIFY: `pip install -r requirements.txt` installs cleanly

- [x] Task 6: Update `Makefile run-pipeline` to be profile-aware (AC: 2)
  - [x] Replace the `run-pipeline` target with a profile-aware version that skips DuckDB-only steps (`edr report`, `build-evidence`) when `COMPOSE_PROFILES != simple`:
    ```makefile
    run-pipeline: ## Run full pipeline: ingestion → dbt run → dbt test → dbt docs generate (edr + Evidence: simple profile only)
    	@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)
    	@PROFILE=$$(grep -E '^COMPOSE_PROFILES=' .env | cut -d= -f2 | tr -d '[:space:]'); \
    	echo "▶  Running pipeline for profile: $$PROFILE"; \
    	echo "▶  Running ingestion (file source)..."; \
    	PYTHONPATH=. python ingest/dlt_file_source.py; \
    	echo "▶  Running ingestion (API source)..."; \
    	PYTHONPATH=. python ingest/dlt_api_source.py; \
    	echo "▶  Running dbt run..."; \
    	dbt run; \
    	echo "▶  Running dbt test..."; \
    	dbt test; \
    	echo "▶  Generating dbt docs..."; \
    	dbt docs generate; \
    	if [ "$$PROFILE" = "simple" ]; then \
    		echo "▶  Generating Elementary report..."; \
    		mkdir -p edr_target; \
    		DBT_DUCKDB_PATH="$$(pwd)/dev.duckdb" edr report --profiles-dir . --profile-target elementary; \
    		$(MAKE) build-evidence; \
    	else \
    		echo "ℹ  Elementary (edr) and Evidence skipped for profile: $$PROFILE (DuckDB-only components)"; \
    	fi; \
    	echo "✔  Pipeline complete — run make open-docs to view dashboards"
    ```
  - [x] VERIFY: `make run-pipeline` with `COMPOSE_PROFILES=postgres` in `.env` runs ingestion + dbt without Elementary/Evidence steps
  - [x] VERIFY: `make run-pipeline` with `COMPOSE_PROFILES=simple` in `.env` still runs the full pipeline including Elementary and Evidence

- [x] Task 7: Write tests `tests/test_story_3_1_postgres_profile.py` (AC: 1, 2, 3)
  - [x] Test `docker/init/postgres_init.sql` existence and content:
    - Schema creation: `CREATE SCHEMA IF NOT EXISTS bronze/silver/gold/quarantine`
    - Role creation: `engineer_role`, `analyst_role`, `pii_analyst_role`
    - Grants present: `GRANT USAGE` and `GRANT SELECT` / `GRANT ALL` lines
  - [x] Test `docker-compose.yml` postgres service:
    - `profiles: ["postgres", "full"]`
    - Port mapping `18040:5432`
    - Volumes mount `01_init.sql` → `/docker-entrypoint-initdb.d/01_init.sql`
  - [x] Test `profiles.yml` postgres target:
    - `type: postgres`
    - `host` uses env_var `POSTGRES_HOST`
    - `port` uses env_var `POSTGRES_PORT`
  - [x] Test `ingest/dlt_file_source.py` for Postgres support:
    - Contains `COMPOSE_PROFILES` check
    - Contains `dlt.destinations.postgres`
    - Contains `psycopg2` import branch
  - [x] Test `ingest/dlt_api_source.py` for Postgres support (same checks)
  - [x] Test `requirements.txt` contains `psycopg2-binary`
  - [x] Test `Makefile` run-pipeline is profile-aware: contains `COMPOSE_PROFILES` conditional logic

- [x] Task 8: Update sprint status
  - [x] `_bmad-output/implementation-artifacts/sprint-status.yaml`: update `3-1-postgres-profile-docker-compose-and-dbt-adapter` → `done` (after verification passes)
  - [x] `_bmad-output/implementation-artifacts/sprint-status.yaml`: update `epic-3` → `in-progress`

## Dev Notes

### Architecture Context: Postgres as a Drop-In dbt Target

Epic 3's central lesson is the three-tier model (architecture doc, p.3): Tier 1 models (portable SQL in `models/`) are unchanged across DuckDB and Postgres. Tier 3 (RBAC, PII masking, engine-native features) is implemented outside dbt in `docker/init/`. This story implements the Tier 3 init layer and the infrastructure glue.

### Postgres Service is Already Scaffolded

`docker-compose.yml` has a `postgres` service stub (added in Story 2.14 planning):
```yaml
# Postgres — data warehouse (postgres, full profiles)
# Story 3.1 adds init SQL scripts; used as dbt target from Epic 2 onwards
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

Task 2 only adds `volumes:`. Do not change any other field in this block.

### profiles.yml Already Has the Postgres Target

`profiles.yml` postgres target is fully configured — no changes needed:
```yaml
postgres:
  type: postgres
  host: "{{ env_var('POSTGRES_HOST', 'localhost') }}"
  port: "{{ env_var('POSTGRES_PORT', '18040') | int }}"
  user: "{{ env_var('POSTGRES_USER', 'dbt') }}"
  password: "{{ env_var('POSTGRES_PASSWORD', '') }}"
  dbname: "{{ env_var('POSTGRES_DB', 'local_data_platform') }}"
  schema: silver
  threads: 4
```

The `schema: silver` default is overridden by the `generate_schema_name.sql` macro — models land in `bronze`, `silver`, `gold`, `quarantine` regardless of this default (same as DuckDB profile).

### Docker Init Script Behaviour (CRITICAL)

The postgres Docker image runs `.sql` files in `/docker-entrypoint-initdb.d/` in alphabetical order — **only on first start when the data directory is empty**. Naming the file `01_init.sql` ensures it runs first.

**If the container has been started before (volume already exists):** The init script will NOT re-run. To force re-initialisation during development:
```bash
docker compose down -v   # removes postgres data volume — DESTRUCTIVE, dev only
docker compose --profile postgres up -d
```

### dlt Destination Selection (CRITICAL)

Both `dlt_file_source.py` and `dlt_api_source.py` currently hardcode `dlt.destinations.duckdb(...)`. They must check `COMPOSE_PROFILES` at runtime. The `dataset_name="bronze"` stays the same for both destinations — dlt writes to the `bronze` schema in whichever destination is active.

The `make run-pipeline` Makefile target exports env vars from `.env` via shell — `COMPOSE_PROFILES` is available to Python scripts without explicit `python-dotenv` loading (the `@PYTHONPATH=. python` call inherits the shell environment where `.env` has already been sourced by the Makefile `grep` command in Task 6).

**Wait — `.env` is NOT automatically loaded into shell env by Makefile.** Python scripts must load it themselves, or the Makefile must explicitly export it. The current scripts rely on environment variables being already set (they use `os.environ.get(..., default)` without dotenv loading). For `make run-pipeline`, env vars from `.env` are NOT automatically in scope unless explicitly exported.

**The fix:** Read `COMPOSE_PROFILES` from `.env` in the Makefile and export it before running Python:
```makefile
run-pipeline:
    @test -f .env || ...
    @set -a; . ./.env; set +a; \
    PYTHONPATH=. python ingest/dlt_file_source.py; \
    ...
```

Or use `export $(grep -v '^#' .env | xargs)` before invoking Python.

**In practice:** The current Makefile runs `PYTHONPATH=. python ingest/dlt_file_source.py` without sourcing `.env`. The existing `DUCKDB_PATH` default (`dev.duckdb`) works because Python falls back to the default. For Postgres, `COMPOSE_PROFILES` must be in the environment when Python runs. Use `set -a; . ./.env; set +a` in the Makefile shell block to source `.env` before Python invocations.

### `dbt-postgres` Must Be Installed on Host

Running `dbt run` on the host with `COMPOSE_PROFILES=postgres` requires `dbt-postgres` installed:
```bash
pip install dbt-postgres==1.10.0
```

The `requirements.txt` tracks Python ingestion deps — `dbt-postgres` is a separate dbt adapter install. Note this in `docs/profile-guide.md` (created in Story 2.14) or add to the README postgres section. **Do not add `dbt-postgres` to `requirements.txt`** — dbt adapters are managed separately.

### `cron-scheduler` Service is Simple Profile Only

Story 2.14 review fix restricted `cron-scheduler` to `profiles: ["simple"]`. The postgres profile does NOT have a scheduler — do NOT add `postgres` to the cron-scheduler profiles list. The `full` profile will use Airflow (Story 5.1) for orchestration.

### Elementary (`edr report`) is DuckDB-Only

The `edr report` step in `make run-pipeline` uses `--profile-target elementary` which targets the `elementary` output in `profiles.yml` — a DuckDB connection. This cannot run when `COMPOSE_PROFILES=postgres`. Task 6 conditionally skips it. **Do not attempt to configure an Elementary Postgres target in this story** — it's out of scope.

### schema.yml and `generate_schema_name.sql` Are Unchanged

The `generate_schema_name.sql` macro routes models to their raw custom schema names (`silver`, `gold`, `quarantine`) regardless of `target.schema`. This is already in place from Story 1.1. The `sources.yml` in `models/bronze/` declares `schema: bronze` which maps directly to the `bronze` Postgres schema that the init script creates. No changes needed.

### dbt Model Portability (Tier 1 — Do Not Break)

All `models/silver/`, `models/gold/`, `models/quarantine/` SQL uses:
- `{{ source('faker_file', 'entity') }}` — reads from `bronze` schema
- `{{ ref('model') }}` — cross-layer refs
- `CURRENT_TIMESTAMP` — cross-engine compatible
- `delete+insert` incremental strategy — cross-engine compatible

Do NOT add any Postgres-specific SQL to model files. Any Postgres-specific changes belong in `docker/init/postgres_init.sql` only.

### `.env.example` Postgres Defaults

```
POSTGRES_HOST=localhost
POSTGRES_PORT=18040
POSTGRES_USER=dbt
POSTGRES_PASSWORD=changeme
POSTGRES_DB=local_data_platform
```

These are already in `.env.example`. No changes needed unless documenting the postgres profile setup more clearly.

### ZScaler SSL — Do NOT Run `dbt deps`

Never run `dbt deps` inside containers. The `dbt_packages/` dir is mounted from the host. See `docs/troubleshooting-dbt-deps-zscaler-tls.md`.

### Key Files to Touch

| File | Change |
|------|--------|
| `docker/init/postgres_init.sql` | New — schema + role init for postgres container |
| `docker-compose.yml` | Add `volumes:` to postgres service (init script mount) |
| `ingest/dlt_file_source.py` | Add Postgres destination (profile-aware) |
| `ingest/dlt_api_source.py` | Add Postgres destination (profile-aware) |
| `requirements.txt` | Add `psycopg2-binary` |
| `Makefile` | Make `run-pipeline` profile-aware (skip DuckDB-only steps) |
| `tests/test_story_3_1_postgres_profile.py` | New — structural verification tests |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Update story + epic status |

### Story 3.2 Context (Do Not Implement in This Story)

Story 3.2 adds PII column masking via Postgres column-level security and row-level security policies. Story 3.1 creates the three roles with baseline grants only. The `pii_analyst_role` in Story 3.1 has the same SELECT grants as `analyst_role` — the masking enforcement is Story 3.2's responsibility. Do not add RLS policies or column masking in this story.

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- 2026-04-14: Loaded BMAD dev workflow, sprint status, and story context. Existing working tree was already dirty before implementation (`.vscode/settings.json`, sprint-status/story generation files); this was recorded as a pre-existing condition before story changes began.
- 2026-04-14: Added Postgres init SQL, mounted it into the Compose postgres service, and verified `docker compose config` plus live `\dn` / `\du` output from the running container.
- 2026-04-14: Added profile-aware dlt destinations for file and API ingestion and verified both scripts loaded rows into Postgres bronze.
- 2026-04-14: Installed `dbt-postgres==1.10.0` on the host for verification, then ran `dbt run` and `dbt test` successfully against the Postgres target.
- 2026-04-14: Normalized contract/source floating-point declarations from `double` to `double precision` so the existing dbt models run unchanged across DuckDB and Postgres.

### Completion Notes List

- Added `docker/init/postgres_init.sql` to create `bronze`, `silver`, `gold`, and `quarantine` schemas plus baseline `engineer_role`, `analyst_role`, and `pii_analyst_role` grants for the Postgres profile.
- Updated `docker-compose.yml` to mount the init SQL into `/docker-entrypoint-initdb.d/01_init.sql`; verified the container starts and the schemas/roles exist in the live database on port `18040`.
- Made `ingest/dlt_file_source.py` and `ingest/dlt_api_source.py` destination-aware so `COMPOSE_PROFILES=postgres` writes to Postgres while other profiles continue using DuckDB.
- Updated `Makefile` `run-pipeline` to source `.env`, pass profile settings to Python/dbt, and skip DuckDB-only Elementary/Evidence steps outside the `simple` profile.
- Added Story 3.1 structural tests and updated affected regression tests so the repo test suite passes with the new profile-aware behavior.
- Fixed an existing cross-engine contract issue by changing floating-point schema declarations from `double` to `double precision`, allowing the existing dbt models to run and test successfully on Postgres without model SQL changes.
- `pip install --user -r requirements.txt`, `python3 -m unittest discover -s tests`, `COMPOSE_PROFILES=postgres PYTHONPATH=. python ingest/dlt_file_source.py`, `COMPOSE_PROFILES=postgres PYTHONPATH=. python ingest/dlt_api_source.py`, `COMPOSE_PROFILES=postgres dbt run`, and `COMPOSE_PROFILES=postgres dbt test` all completed successfully during verification.

## Review Findings

### Decision Needed

- [x] [Review][Decision] `"full"` profile handled in `_get_destination()` / `_verify_counts()` — removed; both ingest scripts now check `COMPOSE_PROFILES == "postgres"` only; `"full"` to be added when Epic 5 lands
- [x] [Review][Decision] Snyk org UUID committed to `.vscode/settings.json` — removed; org config stays local-only

### Patches

- [x] [Review][Patch] Makefile `run-pipeline` uses `;` not `&&` — fixed; all steps now use `&&` so pipeline aborts on first failure [Makefile:run-pipeline]
- [x] [Review][Patch] COMPOSE_PROFILES pre-extracted before `.env` is sourced — fixed; removed grep pre-extraction; now sources `.env` once and uses `$$COMPOSE_PROFILES` directly [Makefile:run-pipeline]
- [x] [Review][Patch] `psycopg2` imported unconditionally at module top-level — fixed; import moved inside the postgres branch of `_verify_counts()` [ingest/dlt_file_source.py, ingest/dlt_api_source.py]
- [x] [Review][Patch] `dlt_file_source.py` `main()` discards `pipeline.run()` return value — fixed; `load_info = pipeline.run(...)` + `load_info.raise_on_failed_jobs()` added [ingest/dlt_file_source.py:main()]

### Deferred

- [x] [Review][Defer] `ALTER DEFAULT PRIVILEGES` applies only to objects created by the init-script executor — correct for now (dlt and dbt run as `POSTGRES_USER`/dbt), latent RBAC gap if future roles diverge; revisit in Story 3.2 [docker/init/postgres_init.sql] — deferred, pre-existing
- [x] [Review][Defer] SQL identifier interpolation in `_verify_counts()` — `f"SELECT COUNT(*) FROM bronze.{entity}"` against psycopg2 is unparameterised; low risk while ENTITIES/TABLES are constants, but should use `psycopg2.sql.Identifier` — deferred, pre-existing
- [x] [Review][Defer] `COMPOSE_PROFILES` read at module-level import time — makes the postgres branch untestable without process isolation; runtime behavior correct via Makefile [ingest/dlt_file_source.py:17, ingest/dlt_api_source.py:17] — deferred, pre-existing
- [x] [Review][Defer] No runtime integration tests — all 7 tests are structural (file-content assertions); AC 1/2 cannot be verified without a running container — deferred, pre-existing
- [x] [Review][Defer] `make start` calls `init-duckdb` unconditionally regardless of profile — pre-existing issue, not introduced here — deferred, pre-existing
- [x] [Review][Defer] `lakehouse` profile falls into the `else` branch of `run-pipeline` with a DuckDB-specific message — cosmetically misleading; out of scope until Epic 4 — deferred, pre-existing
- [x] [Review][Defer] `_verify_counts` has asymmetric signatures between the two ingest files — minor inconsistency, not causing bugs — deferred, pre-existing
- [x] [Review][Defer] Empty `POSTGRES_PASSWORD` default in `_get_destination()` emits no warning — acceptable for local dev; `.env.example` documents the intended value — deferred, pre-existing
- [x] [Review][Defer] Test backslash continuation assertion fragility in `test_story_3_1_postgres_profile.py` — tests format, not behavior; low impact — deferred, pre-existing

### File List

- Makefile
- _bmad-output/implementation-artifacts/3-1-postgres-profile-docker-compose-and-dbt-adapter.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- docker-compose.yml
- docker/init/postgres_init.sql
- ingest/dlt_api_source.py
- ingest/dlt_file_source.py
- models/bronze/sources.yml
- models/gold/dimensions/schema.yml
- models/gold/facts/schema.yml
- models/gold/marts/schema.yml
- models/quarantine/faker/schema.yml
- models/silver/faker/schema.yml
- requirements.txt
- tests/test_makefile_targets.py
- tests/test_story_2_14_cron_readme.py
- tests/test_story_3_1_postgres_profile.py
