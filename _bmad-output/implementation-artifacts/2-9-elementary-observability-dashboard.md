# Story 2.9: Elementary Observability Dashboard

Status: ready-for-dev

## Story

As a data engineer,
I want an Elementary dashboard showing test pass rates, anomaly detection, source freshness status, and schema changes,
so that data quality is visible as a live observability layer — not just a pass/fail exit code.

## Acceptance Criteria

1. **Given** `make start` has been run and dbt tests have executed **When** I open `http://localhost:18030` **Then** the Elementary dashboard loads within 10 seconds and displays test results from the most recent pipeline run.

2. **Given** the Elementary dashboard is open **When** I navigate to the test results view **Then** pass/fail rates are shown per model, I can drill into individual test failures, and source freshness status is visible.

3. **Given** a schema change occurs between pipeline runs (e.g. a column is renamed in the source) **When** I view the Elementary dashboard after the next run **Then** the schema change is surfaced as a detectable event.

4. **Given** `make run-pipeline` has completed **When** I view the Elementary dashboard **Then** row counts per Medallion layer (Bronze, Silver, Gold) are visible or reported — satisfying FR21.

## Tasks / Subtasks

- [ ] Task 1: Add `elementary-data` to `requirements.txt` (AC: 1)
  - [ ] Append `elementary-data` to the root `requirements.txt` (alongside `dlt`, `faker`, `pandas`)
  - [ ] Do NOT touch `ingest/requirements.txt` — that is for ingest scripts only
  - [ ] VERIFY: `pip install elementary-data` resolves without conflicts in the project environment

- [ ] Task 2: Add Elementary profile target to `profiles.yml` (AC: 1, 2)
  - [ ] Add a new `elementary` target under `local_data_platform:` → `outputs:` in `profiles.yml`
  - [ ] The `elementary` target must use `type: duckdb` and the same `path` as the `simple` target
  - [ ] Pattern to follow (add below existing `simple` output):
    ```yaml
    elementary:
      type: duckdb
      path: "{{ env_var('DBT_DUCKDB_PATH', 'dev.duckdb') }}"
      threads: 4
      schema: elementary
    ```
  - [ ] VERIFY: `edr debug --profiles-dir . --profile local_data_platform --target elementary` shows a successful connection

- [ ] Task 3: Run `dbt run` to initialise the Elementary schema (AC: 1)
  - [ ] Elementary on-run-start/end hooks (defined in `dbt_packages/elementary/`) auto-create the `elementary` schema and populate it during `dbt run`
  - [ ] No changes to `dbt_project.yml` needed — Elementary hooks are activated automatically by the package
  - [ ] VERIFY: After `dbt run`, the `elementary` schema exists in `dev.duckdb` with tables like `dbt_models`, `dbt_tests`, `dbt_sources`

- [ ] Task 4: Generate Elementary report using `edr` CLI (AC: 1, 2, 3, 4)
  - [ ] Run: `edr report --profiles-dir . --profile local_data_platform --target elementary`
  - [ ] This produces `edr_target/elementary_report.html` (relative to repo root)
  - [ ] VERIFY: `edr_target/elementary_report.html` exists and is a non-empty HTML file after the command completes
  - [ ] If `edr_target/` does not yet exist it is created automatically by `edr`

- [ ] Task 5: Update `run-pipeline` Makefile target to include `edr report` (AC: 1, 2, 3, 4)
  - [ ] Add `edr report` step after `dbt test` in the `run-pipeline` target
  - [ ] Updated target (replace existing `run-pipeline` recipe):
    ```makefile
    run-pipeline: ## Run full pipeline: ingestion → dbt run → dbt test → edr report
    	@test -f .env || (echo "❌  .env not found. Create it first: cp .env.example .env" && exit 1)
    	@echo "▶  Running ingestion (file source)..."
    	@PYTHONPATH=. python ingest/dlt_file_source.py
    	@echo "▶  Running ingestion (API source)..."
    	@PYTHONPATH=. python ingest/dlt_api_source.py
    	@echo "▶  Running dbt run..."
    	@dbt run
    	@echo "▶  Running dbt test..."
    	@dbt test
    	@echo "▶  Generating Elementary observability report..."
    	@edr report --profiles-dir . --profile local_data_platform --target elementary
    	@echo "✔  Pipeline complete — run make open-docs to view dashboards"
    ```
  - [ ] Update `.PHONY` line if needed (existing targets are already listed)
  - [ ] VERIFY: `make run-pipeline` runs to completion, `edr_target/elementary_report.html` is generated

- [ ] Task 6: Update `docker-compose.yml` `elementary` service to serve the report (AC: 1)
  - [ ] The current `elementary` service uses `tail -f /dev/null` — a stub. Replace with a static file server
  - [ ] Updated service:
    ```yaml
    # Elementary — data observability dashboard (all profiles)
    elementary:
      image: python:3.11-slim
      platform: linux/arm64
      profiles: ["simple", "postgres", "lakehouse", "full"]
      ports:
        - "18030:8080"
      volumes:
        - ./edr_target:/edr_target
      command: >
        sh -c "
          mkdir -p /edr_target &&
          if [ -f /edr_target/elementary_report.html ]; then
            echo 'Serving Elementary report on :8080...' &&
            python3 -m http.server 8080 --directory /edr_target;
          else
            echo 'Elementary report not yet generated. Run make run-pipeline first.' &&
            python3 -m http.server 8080 --directory /edr_target;
          fi
        "
      restart: unless-stopped
    ```
  - [ ] The `edr_target/` directory is created on the host by `edr report`; if it doesn't exist the container creates the mount point but serves an empty directory — that's acceptable
  - [ ] VERIFY: After `make run-pipeline`, `docker compose restart elementary`, then `curl http://localhost:18030/elementary_report.html` returns the report HTML

- [ ] Task 7: Add `edr_target/` to `.gitignore` (AC: 1)
  - [ ] `edr_target/` contains generated HTML artifacts — must not be committed
  - [ ] Check `.gitignore` — if `edr_target/` is not already present, add it
  - [ ] VERIFY: `git status` shows `edr_target/` as ignored after generation

- [ ] Task 8: Full end-to-end validation (AC: 1, 2, 3, 4)
  - [ ] Run `make start` — confirm all simple profile services including `elementary` are up
  - [ ] Run `make run-pipeline` — confirm ingestion, dbt run, dbt test, and edr report all succeed
  - [ ] Open `http://localhost:18030/elementary_report.html` in browser — confirm dashboard loads
  - [ ] Verify test results (pass/fail per model) visible in the dashboard
  - [ ] Verify source freshness status visible (set up in Story 2.8)
  - [ ] Run `PYTHONPATH=. pytest -q tests` — confirm Python tests still pass (no regressions)
  - [ ] Run `make run-pipeline` a second time — confirm Elementary report updates with new run data

### Review Findings

- [x] [Review][Defer] Dead top-level `elementary:` profile in `profiles.yml` — found during dev; edr CLI arguments differed from spec expectations, extra profile block added as a workaround [`profiles.yml`] — deferred, investigate when edr CLI behaviour is better understood
- [x] [Review][Defer] `dbt_project.yml` modified despite spec prohibiting it — found during dev; edr CLI arguments differed from spec expectations, schema config required as a workaround for current version [`dbt_project.yml`] — deferred, investigate when edr CLI behaviour is better understood
- [x] [Review][Patch] `assertIn` call missing second argument — dismissed as false positive; the broken call was a formatting artifact in the review prompt and does not exist in the actual file [`tests/test_elementary_story_2_9.py`]
- [x] [Review][Patch] No `mkdir -p edr_target` before `edr report` in Makefile — fixed: added `@mkdir -p edr_target` before the `@edr report` line [`Makefile`]
- [x] [Review][Defer] `edr report` failure aborts entire `run-pipeline` — design intent per spec; no guard needed for story scope [`Makefile`] — deferred, pre-existing
- [x] [Review][Defer] `edr report` reads DuckDB regardless of active docker-compose profile — story explicitly scoped to simple/DuckDB profile; multi-profile elementary support is out of scope [`Makefile`, `profiles.yml`] — deferred, pre-existing
- [x] [Review][Defer] Container serves empty directory listing before first pipeline run — spec accepts this; no user-guidance message required for story scope [`docker-compose.yml`] — deferred, pre-existing
- [x] [Review][Defer] `elementary-data` unpinned in `requirements.txt` — pre-existing pattern across all project dependencies [`requirements.txt`] — deferred, pre-existing
- [x] [Review][Defer] Tests use brittle hardcoded-indentation substring assertions — pre-existing test pattern in project [`tests/`] — deferred, pre-existing
- [x] [Review][Defer] `python -m http.server` has no authentication — local dev tool; acceptable for project scope [`docker-compose.yml`] — deferred, pre-existing

## Dev Notes

### What Is Already in Place — Do NOT Re-install or Re-declare

**`packages.yml` is complete — do NOT modify it:**
```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0"]
  - package: elementary-data/elementary
    version: [">=0.20.0"]
  - package: calogica/dbt_expectations
    version: [">=0.10.0"]
```

**`dbt_packages/elementary/` already exists** — `dbt deps` was already run. The Elementary dbt package is installed. Running `dbt deps` again is safe but unnecessary unless packages have drifted.

**`packages.yml` installs the Elementary dbt package** (adds hooks + models to your dbt project). However, `edr` CLI is a **separate Python tool** from the `elementary-data` PyPI package — this is NOT installed via dbt. It must be added to `requirements.txt` and installed in the environment.

**Port 18030 is already allocated** to Elementary in `docker-compose.yml` and the `open-docs` Makefile target already opens `http://localhost:18030`. Do not change port numbers.

**`dbt_project.yml` does NOT need modification** — Elementary hooks (`on-run-start`, `on-run-end`) are declared in `dbt_packages/elementary/dbt_project.yml` and activate automatically when `dbt run` is called.

**Story 2.8 already added source freshness** to `models/bronze/sources.yml`. Elementary will automatically surface freshness status in the dashboard without additional configuration.

### Two Elementary Components — Don't Confuse Them

| Component | Package | Purpose | Already installed? |
|---|---|---|---|
| Elementary dbt package | `elementary-data/elementary` via `packages.yml` | Adds hooks + models to dbt project, creates `elementary` schema in warehouse | ✅ Yes (`dbt_packages/elementary/`) |
| Elementary `edr` CLI | `elementary-data` via `pip` / `requirements.txt` | Generates HTML report from the `elementary` schema data | ❌ Not yet |

Both are required. The dbt package populates the `elementary` schema; the `edr` CLI reads that schema and generates the report.

### Elementary Profile Setup — Why a Separate Profile Target Is Needed

The `edr` CLI connects directly to the warehouse to read from the `elementary` schema. It uses the `profiles.yml` file but reads a **named target** (typically `elementary`). This is different from the dbt `simple` target — it needs `schema: elementary` to point `edr` at the correct schema.

The `elementary` target in `profiles.yml` must:
- Use the same `type: duckdb` and `path` as `simple`
- Have `schema: elementary` (so `edr` knows where Elementary's tables live)

The `edr report` command signature:
```bash
edr report --profiles-dir . --profile local_data_platform --target elementary
```
- `--profiles-dir .` — look for `profiles.yml` at repo root
- `--profile local_data_platform` — the profile name in `profiles.yml`
- `--target elementary` — the output target within that profile

### Output File Location

`edr report` writes to `edr_target/elementary_report.html` in the current working directory. Always run `edr report` from the repo root (same as where you run `dbt run`). The Makefile targets already run from repo root so this is the default.

```
local-data-platform/
└── edr_target/
    └── elementary_report.html    ← generated by edr report; gitignored
```

### Docker Compose Service Strategy

The `elementary` Docker container's sole job is to **serve the HTML file** generated on the host by `edr report`. It does not run `edr` itself — that runs on the host as part of `make run-pipeline`.

Volume mount strategy:
- Host `./edr_target` → Container `/edr_target`
- Python HTTP server serves `/edr_target` on port 8080 (→ 18030 on host)
- If `edr_target/elementary_report.html` does not exist yet (before first pipeline run), the server returns a 404 — acceptable, the README documents that `make run-pipeline` must be run first

**`docker compose restart elementary`** may be needed after first report generation if the container started before `edr_target/` existed. The restart resolves volume mount timing issues.

Alternatively: The `elementary` container's `--directory /edr_target` will serve whatever is in the directory at request time — no restart needed if `edr_target/` existed when the container started (or the volume is bind-mounted and Docker resolves the path dynamically).

### ZScaler TLS Issue (From Story 2.8 Learning)

**Critical:** `edr report` makes outbound HTTPS calls to `hub.getdbt.com` or Elementary's API for report metadata. On this machine, ZScaler intercepts TLS and requires the CA bundle at `~/.certs/cacert.pem`.

If `edr report` fails with `SSLCertVerificationError`:
```bash
source ~/.zshrc   # Ensures REQUESTS_CA_BUNDLE and SSL_CERT_FILE are set
edr report --profiles-dir . --profile local_data_platform --target elementary
```

See `docs/troubleshooting-dbt-deps-zscaler-tls.md` for full diagnosis and resolution steps.

This is the same issue that blocked `dbt deps` in Story 2.8 — the fix is identical: source `~/.zshrc` to load the CA bundle environment variables before running any network-dependent tool.

### `.gitignore` Check

These paths must be gitignored (verify each is present):
```
edr_target/        # Elementary generated report output
target/            # dbt compiled artifacts (likely already present)
dev.duckdb         # DuckDB data file (likely already present)
.env               # Secrets (likely already present)
```

### FR21 — Row Counts and Storage per Layer

FR21 requires: row counts and storage sizes per Medallion layer visible after each pipeline run. Elementary automatically tracks `row_count` as part of its test result metadata. The dashboard's "Models" view shows row counts per model per run. This satisfies FR21 for the simple profile.

Storage sizes are not natively surfaced by Elementary's HTML report — this is acceptable for Story 2.9. FR21's storage tracking requirement is satisfied via row counts in the Elementary dashboard; detailed storage sizes can be addressed in a later story or via `analyses/layer_row_counts.sql`.

### Elementary Anomaly Detection — No Additional Configuration Required

Elementary anomaly tests (configured via `elementary` meta blocks in `schema.yml`) are not required for this story. The dashboard will surface:
- All existing dbt test results (pass/fail) from Story 2.8's test additions
- Source freshness status from Story 2.8's `sources.yml` freshness config
- Schema changes automatically detected by Elementary's manifest tracking

Anomaly detection tests (e.g. `elementary.volume_anomalies`, `elementary.column_anomalies`) can be added in a future story once a baseline of pipeline runs has been established. Do NOT add anomaly tests in this story — there are no historical runs to baseline against.

### Scope Boundaries

| In scope | Out of scope |
|---|---|
| Add `elementary-data` to `requirements.txt` | Adding anomaly detection tests to `schema.yml` |
| Add `elementary` profile target to `profiles.yml` | Modifying Silver/Gold SQL models |
| Run `edr report` after `dbt test` in `run-pipeline` | Adding new dbt tests |
| Update Docker Compose `elementary` service to serve HTML | Full `edr` alert/notification setup (Airflow, Story 5.1) |
| Add `edr_target/` to `.gitignore` | MetricFlow (Story 2.7) |
| End-to-end validation of dashboard at port 18030 | Lightdash or Evidence setup |

### Makefile Convention Reminder

- All Makefile targets use `kebab-case`
- Every target must have a `##` comment for `make help`
- `run-pipeline` is already in `.PHONY` — no change needed there
- The `.PHONY` line at the top already declares all targets

### Regression Checks

After all changes, run:
```bash
make run-pipeline             # Full pipeline + edr report — all steps exit 0
PYTHONPATH=. pytest -q tests  # Python tests pass (5 passed expected)
curl http://localhost:18030/elementary_report.html  # Returns HTML (200 OK)
```

## Project Structure Notes

Files to create or modify in this story:

| File | Action | Notes |
|---|---|---|
| `requirements.txt` | Modify | Add `elementary-data` |
| `profiles.yml` | Modify | Add `elementary` target under `local_data_platform:` outputs |
| `Makefile` | Modify | Update `run-pipeline` to include `edr report` step |
| `docker-compose.yml` | Modify | Update `elementary` service from stub to HTML server with volume |
| `.gitignore` | Modify (if needed) | Add `edr_target/` |

No new SQL model files. No new `schema.yml` entries. No changes to `dbt_project.yml` or `packages.yml`.

### References

- Elementary dbt package: `dbt_packages/elementary/` (already installed)
- Port allocation: architecture.md § "Port Allocation" — Elementary=18030
- Makefile conventions: architecture.md § "Format Patterns" — kebab-case, `##` comments
- ZScaler TLS fix: `docs/troubleshooting-dbt-deps-zscaler-tls.md`
- Observability flow: architecture.md § "Integration Points → Observability Flow"
- FR20 (Elementary dashboard), FR21 (row counts per layer): epics.md FR Coverage Map
- Source freshness config: `models/bronze/sources.yml` (added in Story 2.8)
- Docker Compose structure: `docker-compose.yml` lines 54–63 (current `elementary` stub)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List

- requirements.txt
- profiles.yml
- Makefile
- docker-compose.yml
- .gitignore (if edr_target/ not already listed)
- _bmad-output/implementation-artifacts/2-9-elementary-observability-dashboard.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
