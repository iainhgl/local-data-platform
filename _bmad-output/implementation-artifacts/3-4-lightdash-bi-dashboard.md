# Story 3.4: Lightdash BI Dashboard

Status: ready-for-dev

## Story

As a data engineer,
I want Lightdash running against the Postgres Gold schema with pre-built explores,
so that I can browse metrics and dimensions via a dbt-native BI interface without additional manual configuration.

## Acceptance Criteria

1. **Given** `COMPOSE_PROFILES=postgres` is set, `make start` has been run, and `make run-pipeline` has completed,
   **When** I open `http://localhost:18000`,
   **Then** Lightdash loads within 10 seconds and at least one explore is visible based on Gold models.

2. **Given** I navigate to an explore in Lightdash,
   **When** I add a metric and dimension to a chart,
   **Then** results are returned and the underlying SQL references the `gold` schema in Postgres.

3. **Given** `make start` is run on the postgres profile,
   **When** I run `make lightdash-ping`,
   **Then** the command exits 0 and prints a confirmation that Lightdash is healthy.

## Tasks / Subtasks

- [ ] Task 0: Create story branch (AC: all)
  - [ ] `git checkout -b story/3-4-lightdash-bi-dashboard`
  - [ ] Confirm working tree is clean

- [ ] Task 1: Update docker-compose.yml lightdash service (AC: 1, 2)
  - [ ] Add `volumes: - ./:/workspace` to the `lightdash` service (mounts dbt project inside container)
  - [ ] Add warehouse env var overrides for Docker internal networking:
    ```yaml
    - POSTGRES_HOST=postgres
    - POSTGRES_PORT=5432
    - POSTGRES_USER=${POSTGRES_USER}
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    - POSTGRES_DB=${POSTGRES_DB}
    ```
  - [ ] Confirm existing `PGHOST=lightdash-db` / `PG*` vars remain unchanged (they are for the internal metadata DB, NOT the data warehouse)
  - [ ] Add `depends_on` entry for `postgres` service (note: this will cause Compose to error if Lightdash is started without the postgres profile — acceptable, as Lightdash only has data on the postgres/full profiles)
  - [ ] VERIFY: `docker compose --profile postgres config` shows the updated lightdash service correctly

- [ ] Task 2: Create `lightdash.config.yaml` in the project root (AC: 1, 2)
  - [ ] Create `lightdash.config.yaml` at the repo root with the dbt project connection:
    ```yaml
    version: '1.0'
    projects:
      - name: local_data_platform
        type: dbt
        dbt:
          type: local
          project_dir: /workspace
          profiles_dir: /workspace
          profile: local_data_platform
          target: postgres
    ```
  - [ ] VERIFY: File is at the repo root (same level as `dbt_project.yml`)
  - [ ] VERIFY: `project_dir` and `profiles_dir` match the volume mount path (`/workspace`)
  - [ ] VERIFY: `profile` matches `dbt_project.yml` profile name (`local_data_platform`)
  - [ ] VERIFY: `target` is `postgres` (the Postgres dbt target in `profiles.yml`)

- [ ] Task 3: Add `lightdash-ping` Makefile target (AC: 3)
  - [ ] Add `lightdash-ping` to the `.PHONY` line at the top of `Makefile`
  - [ ] Add the target after the `pg-show-pii-log` target (maintain Epic 3 grouping):
    ```makefile
    lightdash-ping: ## Check Lightdash is responding (postgres profile required)
    	@curl -sf http://localhost:18000/api/v1/health | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('status')=='ok' else 1)" && echo "✓ Lightdash healthy at http://localhost:18000" || echo "✗ Lightdash not responding — is the postgres profile running?"
    ```
  - [ ] VERIFY: `make lightdash-ping` exits 0 when Lightdash is running
  - [ ] VERIFY: `make help` shows the `lightdash-ping` target with description

- [ ] Task 4: Write tests `tests/test_story_3_4_lightdash.py` (AC: 1, 2, 3)
  - [ ] Test that `lightdash.config.yaml` exists at the project root
  - [ ] Test that `lightdash.config.yaml` contains required keys: `version`, `projects`, `type: dbt`, `project_dir: /workspace`, `profiles_dir: /workspace`, `profile: local_data_platform`, `target: postgres`
  - [ ] Test that `docker-compose.yml` lightdash service has a volume mount for `./:/workspace`
  - [ ] Test that `docker-compose.yml` lightdash service overrides `POSTGRES_HOST=postgres` for Docker internal networking
  - [ ] Test that `docker-compose.yml` lightdash service passes through `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` env vars
  - [ ] Test that `lightdash-ping` is declared in `Makefile` `.PHONY` line

- [ ] Task 5: Update sprint status
  - [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml`: update `3-4-lightdash-bi-dashboard` → `done` after verification passes

## Dev Notes

### Why This Story Exists (Deferred from 2.10)

Story 2.10 was deferred because Lightdash upstream does not support DuckDB as a warehouse target. With Postgres now available (Epic 3), Lightdash can connect to the Gold schema as a first-class warehouse. **Story 3.4 is the implementation of Story 2.10, scoped to the Postgres profile.**

### What Is Already in Place (Do NOT Change)

The `lightdash` and `lightdash-db` services are already declared in `docker-compose.yml`. The current state:
- `lightdash-db` — Lightdash's internal metadata Postgres database (stores project configs, user sessions). **Do NOT touch this.**
- `lightdash` — runs `lightdash/lightdash:latest` (amd64 only; runs under Rosetta 2 on Apple Silicon — this is NFR11 known exception). Already has: `LIGHTDASH_SECRET`, `PGHOST=lightdash-db`, `PGPORT`, `PGUSER=lightdash`, `PGPASSWORD`, `PGDATABASE=lightdash_db`.

All Gold models already have `contract: enforced: true`, `data_type` declarations, `constraints:`, and `meta.pii` tags. These are exactly what Lightdash reads to build explores. **Do NOT touch any Gold schema.yml files.**

### Critical: Two Postgres Connections in One Service

The Lightdash container uses **two separate Postgres connections**:

| Variable | Points to | Purpose |
|---|---|---|
| `PGHOST=lightdash-db` | `lightdash-db` Docker service | Lightdash metadata DB (sessions, config) |
| `POSTGRES_HOST=postgres` | `postgres` Docker service | **The data warehouse (Gold schema)** |

These must NOT be confused. The `PG*` vars (existing) serve the metadata DB. The `POSTGRES_*` vars (added by this story) serve the data warehouse and are read by `profiles.yml` via `env_var()`.

### Docker Networking: Host vs Container

`profiles.yml` uses `env_var('POSTGRES_HOST', 'localhost')` and `env_var('POSTGRES_PORT', '18040')`. These defaults are correct for **host-machine** dbt access (through the published port). Inside the Lightdash container, the Postgres service is reachable at `postgres:5432` (Docker service name + internal port).

| Context | POSTGRES_HOST | POSTGRES_PORT |
|---|---|---|
| Host machine (`dbt run` from terminal) | `localhost` (from `.env`) | `18040` (from `.env`) |
| Lightdash container (dbt via profiles.yml) | `postgres` (set in docker-compose.yml) | `5432` (Docker internal) |

**Do NOT change `.env.example`** — the host-side values are correct. Override only inside the container via `docker-compose.yml` environment block.

### `lightdash.config.yaml` Role

This file tells the Lightdash application where to find the dbt project inside the container. The `project_dir` and `profiles_dir` must match the volume mount path (`/workspace`). Lightdash reads this file on startup, connects to the dbt project, and compiles explores from the Gold models' `schema.yml` definitions.

`lightdash.config.yaml` is placed at the **repo root** (same level as `dbt_project.yml`). The volume mount `./:/workspace` makes it available inside the container at `/workspace/lightdash.config.yaml`.

### Gold Models Are Already Explore-Ready

The Gold models (`fct_orders`, `dim_customers`, `dim_products`, `orders_mart`) have:
- Full column documentation in `schema.yml` (descriptions, `data_type`, `meta.pii`)
- `contract: enforced: true` ensuring stable schemas
- `constraints:` on primary keys (Story 3.3)
- Tags: `tag: gold`

Lightdash reads `schema.yml` to build explores — no additional model changes required.

### Profile-Awareness Consideration

The `lightdash` service currently has `profiles: ["simple", "postgres", "lakehouse", "full"]`. This story adds `depends_on: postgres`, which means starting Lightdash on the `simple` profile will fail. This is acceptable because:
1. Lightdash has no warehouse connection on the simple profile anyway (DuckDB not supported)
2. The port 18000 is still accessible on all profiles via the existing `open-docs` target
3. If profile-less operation is needed in future, remove `depends_on: postgres` then — that's a separate story

Document this change in the docker-compose.yml comment: `# Warehouse connection requires postgres service; Lightdash is only fully functional on postgres/full profiles.`

### Makefile Pattern (from Stories 3.1–3.3)

Always update `.PHONY` when adding a new target. Add the new target after the last Epic 3 target (`dbt-verify-contracts`). Follow the `kebab-case` naming convention. Every target must have a `##` comment for `make help`.

### Test Patterns (from Stories 3.1–3.3)

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]

class Story34LightdashTests(unittest.TestCase):
    ...
```

- Tests use `yaml.safe_load()` for YAML files, `Path.read_text()` for string assertions
- No DB connectivity required — all tests are structural (file content assertions)
- Use `next(..., None)` + `assertIsNotNone` to avoid `StopIteration` exceptions
- Test class naming: `Story3{N}DescriptiveNameTests` → use `Story34LightdashTests`

For testing the `lightdash.config.yaml`:
```python
import yaml
config = yaml.safe_load((PROJECT_ROOT / "lightdash.config.yaml").read_text())
projects = config["projects"]
dbt_config = projects[0]["dbt"]
self.assertEqual(dbt_config["project_dir"], "/workspace")
self.assertEqual(dbt_config["target"], "postgres")
```

For testing docker-compose.yml additions, use string assertions:
```python
compose = (PROJECT_ROOT / "docker-compose.yml").read_text()
self.assertIn("- ./:/workspace", compose)
self.assertIn("POSTGRES_HOST=postgres", compose)
```

### Files to Touch

| File | Change |
|------|--------|
| `docker-compose.yml` | Add volume mount + warehouse env vars to `lightdash` service; update comment; add `depends_on: postgres` |
| `lightdash.config.yaml` | New file — dbt project connection config |
| `Makefile` | Add `lightdash-ping` target; update `.PHONY` |
| `tests/test_story_3_4_lightdash.py` | New — structural verification tests |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Update story status to `done` |

**Do NOT touch:**
- `docker/init/postgres_init.sql` — Story 3.1 RBAC baseline
- `docker/init/postgres_masking.sql` — Story 3.2 masking
- Any `schema.yml` files — Gold models are already explore-ready
- Any `.sql` model files — no model changes needed
- `profiles.yml` — env var structure already correct; host-side values come from `.env`
- `.env.example` — host-side values are correct; warehouse env vars are overridden in docker-compose.yml
- `requirements.txt` — no new Python dependencies

### Verification Commands

```bash
# Check Lightdash health via API
curl -sf http://localhost:18000/api/v1/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)"

# Run structural tests
python -m unittest tests/test_story_3_4_lightdash.py

# Run all tests
python -m unittest discover tests

# Validate Compose config (check lightdash service env and volumes)
docker compose --profile postgres config | grep -A 40 "lightdash:"

# Start with postgres profile
COMPOSE_PROFILES=postgres make start

# Run pipeline to populate Gold schema
make run-pipeline

# Ping Lightdash
make lightdash-ping

# Open browser
make open-docs
```

### Previous Story Intelligence (Stories 3.1–3.3)

- Story 3.1 pattern: Add `depends_on` to new services; use Docker service names for inter-container networking
- Story 3.2 pattern: `COMPOSE_PROFILES=postgres` guard in Makefile targets that require Postgres
- Story 3.3 confirmed: `dbt compile --select tag:gold` works as a connectivity-free verification step
- Consistent test naming: `Story3{N}...Tests`; `PROJECT_ROOT = Path(__file__).resolve().parents[1]`
- `.PHONY` must be on a single line — parse it then assert membership, not substring position (see Story 3.3 review finding)

### Architecture References

- [Source: `_bmad-output/planning-artifacts/architecture.md`, Port Allocation Map] — Lightdash=18000, all profiles
- [Source: `_bmad-output/planning-artifacts/architecture.md`, Data Flow] — `Lightdash / Evidence / Superset (direct warehouse connection)`
- [Source: `_bmad-output/planning-artifacts/architecture.md`, Docker Service Naming] — `lightdash` (lowercase-hyphenated)
- [Source: `_bmad-output/planning-artifacts/architecture.md`, Env Var Naming] — `LIGHTDASH_*` prefix, `SCREAMING_SNAKE_CASE`
- [Source: `_bmad-output/planning-artifacts/epics.md`, Story 2.10] — Original Lightdash ACs (explores visible, SQL references Gold)
- [Source: `_bmad-output/implementation-artifacts/sprint-status.yaml`] — Story moved from 2-10; Postgres is first-class Lightdash target

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List

### Change Log
