# Story 2.14: Cron Schedule and README

Status: done

## Story

As a data engineer,
I want the `simple` profile to run the pipeline on a cron schedule and the README to provide everything needed for a first-time learner to get started,
so that the pipeline runs automatically after `make start` and a new learner can be productive within 10 minutes of cloning.

## Acceptance Criteria

1. **Given** `make start` has been run on the `simple` profile, **When** the `CRON_INTERVAL` elapses, **Then** the pipeline executes automatically (ingestion → dbt run → dbt test → dbt docs generate) without manual `make run-pipeline` invocation (FR7).

2. **Given** a new learner clones the repository, **When** they read the README, **Then** it contains: hardware requirements (8 GB min / 16 GB recommended), quick-start instructions (clone → copy .env → make start), profile descriptions, cloud equivalence table summary, and WSL2 compatibility notes (FR48, NFR18).

3. **Given** the cloud equivalence table (in `docs/cloud-equivalence.md`), **When** I inspect it, **Then** every local component (DuckDB, dlt, dbt, MinIO, Trino, Airflow, Keycloak, Prometheus/Grafana, Superset, Elementary, Evidence, OpenMetadata) maps to its cloud/SaaS equivalent (FR46).

## Tasks / Subtasks

- [x] Task 0: Create story branch
  - [x] `git checkout -b story/2-14-cron-schedule-and-readme`
  - [x] Confirm working tree is clean

- [x] Task 1: Create `docker/scheduler/Dockerfile` (AC: 1)
  - [x] Create directory `docker/scheduler/`
  - [x] Write `docker/scheduler/Dockerfile`:
    ```dockerfile
    FROM python:3.11-slim
    WORKDIR /workspace
    RUN pip install --no-cache-dir \
        dbt-duckdb \
        "dlt[filesystem]" \
        faker \
        pandas
    COPY docker/scheduler/run_pipeline.sh /run_pipeline.sh
    RUN chmod +x /run_pipeline.sh
    ```
  - [x] VERIFY: `docker build -f docker/scheduler/Dockerfile -t scheduler-test .` builds successfully (ARM64 required — NFR11)

- [x] Task 2: Create `docker/scheduler/run_pipeline.sh` (AC: 1)
  - [x] Write the pipeline script:
    ```bash
    #!/bin/sh
    set -e
    cd /workspace
    echo "▶  [cron] Running ingestion (file source)..."
    PYTHONPATH=/workspace python ingest/dlt_file_source.py
    echo "▶  [cron] Running ingestion (API source)..."
    PYTHONPATH=/workspace python ingest/dlt_api_source.py
    echo "▶  [cron] Running dbt run..."
    dbt run --profiles-dir /workspace
    echo "▶  [cron] Running dbt test..."
    dbt test --profiles-dir /workspace
    echo "▶  [cron] Generating dbt docs..."
    dbt docs generate --profiles-dir /workspace
    echo "✔  [cron] Pipeline complete at $(date)"
    ```
  - [x] Note: Evidence build (`npm run build`) and Elementary report (`edr report`) are excluded — both have ARM64/host-only constraints documented in Stories 2.11 and 2.9 respectively. The cron pipeline covers the core: ingestion → dbt run → test → docs.

- [x] Task 3: Add `cron-scheduler` service to `docker-compose.yml` (AC: 1)
  - [x] Add service under the `simple` (and `postgres`, `lakehouse`, `full`) profiles, after the `dbt-docs` service:
    ```yaml
      # cron-scheduler — runs the pipeline on a schedule (all profiles)
      # Story 2.14 wires this service. Evidence build and Elementary edr report run on host only.
      cron-scheduler:
        build:
          context: .
          dockerfile: docker/scheduler/Dockerfile
        platform: linux/arm64
        profiles: ["simple", "postgres", "lakehouse", "full"]
        volumes:
          - ./:/workspace
        environment:
          - COMPOSE_PROFILES=${COMPOSE_PROFILES:-simple}
          - DBT_DUCKDB_PATH=/workspace/${DBT_DUCKDB_PATH:-dev.duckdb}
          - FAKER_ROWS=${FAKER_ROWS:-1000}
          - FAKER_OUTPUT_DIR=${FAKER_OUTPUT_DIR:-data}
          - API_BASE_URL=${API_BASE_URL:-https://jsonplaceholder.typicode.com}
          - CRON_INTERVAL=${CRON_INTERVAL:-3600}
        command: >-
          sh -c "echo '▶  Scheduler starting — interval: ${CRON_INTERVAL:-3600}s' &&
                 /run_pipeline.sh &&
                 while true; do sleep ${CRON_INTERVAL:-3600}; /run_pipeline.sh; done"
        restart: unless-stopped
    ```
  - [x] Note the `DBT_DUCKDB_PATH` override: the compose service must use the **absolute container path** `/workspace/dev.duckdb` because `profiles.yml` defaults to the relative `dev.duckdb` — overriding via env var avoids editing profiles.yml.
  - [x] VERIFY: `docker compose build cron-scheduler` succeeds
  - [x] VERIFY: `docker compose up -d cron-scheduler` starts; `docker compose logs cron-scheduler` shows the pipeline running on first start

- [x] Task 4: Add `CRON_INTERVAL` to `.env.example` (AC: 1)
  - [x] Append to `.env.example` under a `# Cron Scheduler` section:
    ```
    # Cron Scheduler (Story 2.14)
    # Interval in seconds between automatic pipeline runs (default: 3600 = 1 hour)
    # Set to 0 to disable scheduled runs (manual make run-pipeline only)
    CRON_INTERVAL=3600
    ```

- [x] Task 5: Complete README quick-start section (AC: 2)
  - [x] Replace the placeholder comment `<!-- Full quick-start instructions added in Story 2.14 -->` under `## Quick Start` with:
    ```markdown
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

    > **Prerequisites:** Docker Desktop, Python 3.11+, dbt-duckdb, dlt — see [Hardware Requirements](#hardware-requirements) below.
    ```

- [x] Task 6: Add profile descriptions to README (AC: 2)
  - [x] Add a `## Profiles` section to README (after `## Quick Start`, before `## Sprint Status`):
    ```markdown
    ## Profiles

    Set `COMPOSE_PROFILES` in `.env` to switch profiles. All profiles share the same dbt models, ingestion scripts, and `schema.yml`.

    | Profile | Query Engine | Use Case |
    |---|---|---|
    | `simple` | DuckDB (file-based) | Local learning — minimal footprint, no auth |
    | `postgres` | Postgres (Docker) | Server warehouse, three-role RBAC, PII masking |
    | `lakehouse` | Trino + MinIO + Iceberg | Open table formats, schema evolution, large datasets |
    | `full` | All of the above | Enterprise stack — Airflow, Keycloak SSO, Superset, MCP |

    See [docs/profile-guide.md](docs/profile-guide.md) for per-profile hardware and service details.
    ```

- [x] Task 7: Add WSL2 and cloud equivalence references to README (AC: 2, 3)
  - [x] Add a `## WSL2 (Windows)` section (brief, before or after Port Allocation):
    ```markdown
    ## WSL2 (Windows)

    The platform runs on WSL2 (Ubuntu 22.04+). Set Docker Desktop → Settings → Resources → "Use WSL 2 based engine". See [docs/wsl2.md](docs/wsl2.md) for full setup and known limitations.
    ```
  - [x] Add a `## Cloud Equivalence` section (before Port Allocation or after Profiles):
    ```markdown
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
    ```

- [x] Task 8: Create `docs/cloud-equivalence.md` (AC: 3, FR46)
  - [x] Create the file with: full equivalence table (same rows as README summary above plus additional columns: "Pattern", "Cloud migration notes"), a brief intro, and the full list of all services/tools
  - [x] Reference this file from README `## Cloud Equivalence` section (link already added in Task 7)

- [x] Task 9: Create `docs/wsl2.md` (AC: 2, FR48)
  - [x] Create the file with:
    - Prerequisites: WSL2 + Ubuntu 22.04+, Docker Desktop with WSL2 backend
    - Docker Desktop settings needed
    - Known limitation: DuckDB file path — use `/mnt/c/...` or clone inside WSL2 filesystem
    - WSL2 memory: add `[wsl2]\nmemory=8GB` to `%USERPROFILE%\.wslconfig`
    - Port access from Windows browser: `localhost` works via WSL2 port forwarding

- [x] Task 10: Create `docs/profile-guide.md` (AC: 2)
  - [x] Create the file with per-profile hardware requirements, service list, and startup commands
  - [x] One section per profile: `simple`, `postgres`, `lakehouse`, `full`

- [x] Task 11: Update sprint status and README sprint table (AC: 2)
  - [x] README: change `2.14 | Cron schedule and README | backlog` → `done`
  - [x] `sprint-status.yaml`: update `2-14-cron-schedule-and-readme` → `done`

## Dev Notes

### Cron Scheduler Architecture

**Why a Docker service, not host crontab:** The AC requires the pipeline to run automatically after `make start` — no post-clone user configuration should be needed. A Docker Compose service satisfies this without requiring `crontab -e` on the host.

**Why a sleep loop, not supercronic:** `supercronic` requires downloading an ARM64 binary in the Dockerfile (adds fragility, version pinning). A shell `sleep` loop is transparent, has no additional dependencies, and is sufficient for a learning platform with hourly granularity.

**Why `set -e` in `run_pipeline.sh`:** The script must exit non-zero on failure so `docker compose logs` surfaces the error clearly and the loop does not silently continue to sleep after a failed run.

**DuckDB path override (CRITICAL):** `profiles.yml` defaults `DBT_DUCKDB_PATH` to `dev.duckdb` (relative path). Inside the container, the working directory is `/workspace` so `dev.duckdb` resolves to `/workspace/dev.duckdb` correctly — BUT the compose `environment:` block must override `DBT_DUCKDB_PATH=/workspace/dev.duckdb` (absolute) to be explicit and safe regardless of how dbt resolves paths.

**DuckDB write-lock warning:** Only one process can write to `dev.duckdb` at a time. Do NOT run `make run-pipeline` from the host while the cron-scheduler container is actively running the pipeline — both will race for the DuckDB write lock and one will fail. The cron container logs `[cron] Pipeline complete at <timestamp>` when finished.

**Evidence and Elementary excluded from cron:** Evidence build (`npm run build`) hangs on `linux/arm64` inside Docker (documented in Story 2.11). Elementary's `edr report` requires host-level authentication and was scoped to host-only in Story 2.9. Both remain manual-only operations via `make run-pipeline`.

**ARM64 validation (NFR11):** `python:3.11-slim` has native `linux/arm64` support. All pip packages (`dbt-duckdb`, `dlt`, `faker`, `pandas`) have ARM64 wheels. Build must succeed on Apple Silicon without Rosetta.

### Key Files to Touch

| File | Change |
|------|--------|
| `docker/scheduler/Dockerfile` | New — scheduler image |
| `docker/scheduler/run_pipeline.sh` | New — pipeline shell script |
| `docker-compose.yml` | Add `cron-scheduler` service |
| `.env.example` | Add `CRON_INTERVAL` |
| `README.md` | Fill Quick Start; add Profiles, Cloud Equivalence, WSL2 sections |
| `docs/cloud-equivalence.md` | New — full equivalence table |
| `docs/wsl2.md` | New — WSL2 setup guide |
| `docs/profile-guide.md` | New — per-profile hardware and service guide |

### `profiles.yml` — Container Behaviour

The `profiles.yml` at repo root reads `COMPOSE_PROFILES` to select the dbt target. Inside the cron container, `COMPOSE_PROFILES=simple` (passed via compose `environment:`) selects the DuckDB target automatically. No changes to `profiles.yml` required.

### `dbt_project.yml` Location

`dbt_project.yml` lives at repo root (`/workspace/dbt_project.yml` inside the container). dbt auto-discovers `dbt_project.yml` from the working directory (`WORKDIR /workspace`). No `--project-dir` flag needed.

### `dbt_packages/` Must Exist

The container must have `dbt_packages/` available — it is mounted from the host repo (volume: `./:/workspace`). Do NOT run `dbt deps` inside the container — see ZScaler SSL note. The packages are already on disk from the host install.

### ZScaler SSL — Do NOT run `dbt deps`

Never run `dbt deps` inside the container or during testing. Use existing `dbt_packages/` on disk (they are mounted via the volume). See `docs/troubleshooting-dbt-deps-zscaler-tls.md`.

### ingest Scripts — DLT Config

`dlt_file_source.py` and `dlt_api_source.py` both read from `.env` via `python-dotenv` if available, or fall back to environment variables. The compose `environment:` block provides all required vars. Verify `FAKER_OUTPUT_DIR=data` resolves correctly inside the container (the `data/` dir is at `/workspace/data/`).

### README Style

- Use existing section structure (H2 headings, pipe tables)
- No emojis — consistent with existing README style
- Keep Quick Start to ≤6 numbered steps
- Cloud equivalence table: ≤12 rows in README; full detail in `docs/cloud-equivalence.md`

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `python3 -m pytest -q tests/test_story_2_14_cron_readme.py` (red: 4 failing assertions, then green)
- `python3 -m pytest -q tests/test_story_2_14_cron_readme.py tests/test_makefile_targets.py tests/test_elementary_story_2_9.py tests/test_story_2_11_evidence.py`
- `docker compose config >/tmp/story-2-14-compose-config.out && echo OK`
- `docker compose build cron-scheduler`
- `docker compose up -d cron-scheduler`
- `docker compose logs cron-scheduler --tail 200`
- `docker compose stop cron-scheduler`

### Completion Notes List

- Added a dedicated ARM64 scheduler image and `/run_pipeline.sh` entrypoint for automated ingestion, dbt run, dbt test, and dbt docs generation.
- Added the `cron-scheduler` compose service with profile coverage for `simple`, `postgres`, `lakehouse`, and `full`, plus `CRON_INTERVAL` support and `CRON_INTERVAL=0` disable behaviour.
- Expanded `README.md` with a concrete quick start, profile guide summary, cloud equivalence summary, WSL2 guidance, and updated Story 2.14 sprint-row status.
- Added `docs/cloud-equivalence.md`, `docs/wsl2.md`, and `docs/profile-guide.md` to support first-time learners.
- Added `tests/test_story_2_14_cron_readme.py` and kept the existing story regression tests green.
- During runtime verification, discovered `requests` was required by `ingest/dlt_api_source.py`; added it to the scheduler image and `requirements.txt` so the scheduled container can complete the full pipeline successfully.
- The worktree was not clean at start because unrelated user-owned changes already existed (`.vscode/settings.json`, sprint artifact updates, and local worktree directories). I worked around them without reverting anything.

## Review Findings

- [x] [Review][Patch] `cron-scheduler` declared on all profiles but Dockerfile only installs `dbt-duckdb` — fails on `postgres`/`lakehouse`/`full`; FIXED: restricted to `profiles: ["simple"]`; full profile uses Airflow (Story 5.1) [docker-compose.yml]
- [x] [Review][Patch] `DBT_DUCKDB_PATH=/workspace/${DBT_DUCKDB_PATH:-dev.duckdb}` double-path bug; FIXED: replaced with literal `/workspace/dev.duckdb` [docker-compose.yml]
- [x] [Review][Patch] No `dbt_packages/` pre-flight guard in `run_pipeline.sh`; FIXED: added existence check with clear error message before first dbt call [docker/scheduler/run_pipeline.sh]
- [x] [Review][Defer] DuckDB write-lock race if host `make run-pipeline` runs concurrently with cron container — deferred, documented in story Dev Notes; pre-existing across all dbt commands
- [x] [Review][Defer] Pipeline fires immediately on container start before first interval elapses — deferred, intentional UX choice for a learning tool; better than a silent first hour wait
- [x] [Review][Defer] `restart: unless-stopped` + `set -e` creates tight crash-restart loop on pipeline failure — deferred, pre-existing pattern across all services (elementary, dbt-docs)
- [x] [Review][Defer] No version pins in `docker/scheduler/Dockerfile` — deferred, pre-existing project convention; `requirements.txt` also unpinned

### File List

- .env.example
- README.md
- _bmad-output/implementation-artifacts/2-14-cron-schedule-and-readme.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- docker-compose.yml
- docker/scheduler/Dockerfile
- docker/scheduler/run_pipeline.sh
- docs/cloud-equivalence.md
- docs/profile-guide.md
- docs/wsl2.md
- requirements.txt
- tests/test_story_2_14_cron_readme.py
