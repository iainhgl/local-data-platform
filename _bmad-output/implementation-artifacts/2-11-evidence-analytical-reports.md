# Story 2.11: Evidence Analytical Reports

Status: done

## Story

As a data engineer,
I want Evidence reports committed to the repository as code,
so that I can see version-controlled, reproducible analytical outputs alongside the pipeline code.

## Acceptance Criteria

1. **Given** `make start` has been run and `make run-pipeline` has completed **When** I open `http://localhost:18010` **Then** the Evidence app loads and displays at least one report showing pipeline output data from the Gold layer.

2. **Given** the Evidence report files in the repository **When** I inspect them **Then** they are SQL + Markdown `.md` files committed to source control — not generated artifacts — and the data they display is sourced from the Gold layer models (`gold.orders_mart`, `gold.fct_orders`, `gold.dim_customers`, or `gold.dim_products`).

## Tasks / Subtasks

- [x] Task 1: Scaffold the Evidence project in the `evidence/` subdirectory (AC: 1, 2)
  - [x] Run from repo root: `npx degit evidence-dev/template evidence/`
  - [x] This creates `evidence/package.json`, `evidence/evidence.plugins.yaml`, `evidence/pages/index.md`, and `evidence/sources/` scaffold
  - [x] If ZScaler TLS blocks npx: `source ~/.zshrc` first to load CA bundle env vars (same fix as dbt deps in Story 2.8)
  - [x] Do NOT commit `evidence/node_modules/` — ensure `evidence/node_modules/` is in `.gitignore`
  - [x] VERIFY: `evidence/package.json` exists after scaffold completes

- [x] Task 2: Add `@evidence-dev/duckdb` connector and configure DuckDB source (AC: 1, 2)
  - [x] Update `evidence/evidence.plugins.yaml` to register the DuckDB plugin:
    ```yaml
    components:
      "@evidence-dev/core-components": {}
    plugins:
      "@evidence-dev/duckdb": {}
    ```
  - [x] Create directory `evidence/sources/local_duckdb/`
  - [x] Create `evidence/sources/local_duckdb/connection.yaml`:
    ```yaml
    name: local_duckdb
    type: duckdb
    options:
      filename: ../dev.duckdb
    ```
  - [x] The `filename` path is **relative to the `sources/local_duckdb/` directory** — `../dev.duckdb` resolves to `evidence/dev.duckdb`; the Docker Compose env var override (Task 4) sets the correct absolute path inside the container
  - [x] VERIFY: `connection.yaml` is committed; `connection.options.yaml` does not need to exist for DuckDB (no secrets)

- [x] Task 3: Create at least one Gold layer report page (AC: 1, 2)
  - [x] Create `evidence/pages/index.md` as the pipeline summary home page:
    ```markdown
    ---
    title: Local Data Platform — Pipeline Reports
    ---

    # Pipeline Reports

    Data from the most recent `make run-pipeline` run.

    - [Orders Summary](/gold/orders-summary) — order volumes, revenue, and return rates from the Gold layer
    ```
  - [x] Create directory `evidence/pages/gold/`
  - [x] Create `evidence/pages/gold/orders-summary.md` as the primary report (see Dev Notes for content)
  - [x] Report `.md` files ARE committed to source control — this satisfies AC2
  - [x] Do NOT add any generated files under `evidence/.evidence/` to source control (add to `.gitignore`)
  - [x] VERIFY: At least `index.md` and `pages/gold/orders-summary.md` exist and are committed

- [x] Task 4: Update `docker-compose.yml` Evidence service (AC: 1)
  - [x] Replace the current Evidence stub:
    ```yaml
    # Evidence — analytical reporting (all profiles)
    evidence:
      image: evidencedev/devenv:latest
      platform: linux/amd64
      profiles: ["simple", "postgres", "lakehouse", "full"]
      ports:
        - "18010:3000"
      volumes:
        - ./:/evidence-workspace
      working_dir: /evidence-workspace/evidence
      environment:
        - EVIDENCE_SOURCE__local_duckdb__filename=/evidence-workspace/dev.duckdb
      restart: unless-stopped
    ```
  - [x] **Image note:** `evidencedev/devenv:latest` is the documented Evidence Docker dev image (from `evidence-dev/docker-devenv`). If `ghcr.io/evidence-dev/evidence:latest` turns out to be the correct current image, use that — but verify it accepts the same working_dir/env var conventions before committing
  - [x] **Platform note:** Changed from `linux/arm64` to `linux/amd64` — DuckDB native bindings require amd64; runs under Rosetta 2 on Apple Silicon (same pattern as Lightdash — see docker-compose.yml comment on `lightdash` service)
  - [x] **Volume:** `./:/evidence-workspace` mounts the entire repo root. The `EVIDENCE_SOURCE__local_duckdb__filename` env var overrides the relative `filename` in `connection.yaml` with an absolute container path
  - [x] **working_dir:** `/evidence-workspace/evidence` — the container's default entrypoint runs `npm install && npm run dev` from this directory
  - [x] VERIFY: `docker compose --profile simple up evidence` starts the container; check logs that `npm run dev` is running on port 3000

- [x] Task 5: Update `.gitignore` for Evidence artifacts (AC: 2)
  - [x] Add the following to `.gitignore` (check if already present before adding):
    ```
    evidence/node_modules/
    evidence/.evidence/
    evidence/.env
    ```
  - [x] `evidence/node_modules/` — npm packages installed by the container (not committed)
  - [x] `evidence/.evidence/` — Evidence build cache and compiled query results (not committed)
  - [x] VERIFY: `git status` shows Evidence report `.md` files as tracked, and `node_modules`/`.evidence/` as ignored

- [x] Task 6: End-to-end validation (AC: 1, 2)
  - [x] Run `make start` — confirm Evidence service starts (check `docker compose logs evidence`)
  - [x] Allow 60–90 seconds for `npm install` to complete on first container start (downloads dependencies)
  - [x] Run `make run-pipeline` — confirm pipeline completes with data in Gold layer
  - [x] Open `http://localhost:18010` — confirm Evidence home page loads
  - [x] Navigate to `/gold/orders-summary` — confirm report shows data from `gold.orders_mart`
  - [x] Confirm report SQL files are in `evidence/pages/` and committed to source control
  - [x] Run `PYTHONPATH=. pytest -q tests` — confirm no regressions
  - [x] Run `make open-docs` — confirm Evidence opens at `http://localhost:18010` (target already exists in Makefile)

### Review Findings

- [x] [Review][Patch] QEMU core dumps not gitignored — added `evidence/*.core` to root `.gitignore` [`.gitignore`]
- [x] [Review][Patch] `needful_things` source has no backing DuckDB file — removed `evidence/sources/needful_things/` directory [`evidence/sources/`]
- [x] [Review][Defer] Dual plugin config files (`evidence.plugins.yaml` + `evidence.config.yaml`) with different key formats — scaffold generated `evidence.config.yaml` (newer `datasources:` format); dev added `evidence.plugins.yaml` (older `plugins:` format); Evidence v40 may use either; container appears functional; investigate once runtime verified [`evidence/`] — deferred, investigate
- [x] [Review][Defer] Evidence container starts before pipeline has run — no `depends_on`; Evidence shows empty data on first start before `make run-pipeline`; design intent; AC precondition is pipeline completion [`docker-compose.yml`] — deferred, pre-existing
- [x] [Review][Defer] Bloated `package.json` with 12 unused connector dependencies — template scaffold default; story says don't modify `package.json`; increases npm install time but `node_modules` is volume-mounted and cached [`evidence/package.json`] — deferred, pre-existing template default
- [x] [Review][Defer] Concurrent DuckDB access during pipeline run — pre-existing pattern shared with Elementary; DuckDB allows concurrent reads; no write contention during Evidence page loads [`docker-compose.yml`] — deferred, pre-existing

## Dev Notes

### Evidence Architecture — Two Separate Things

Evidence has two distinct parts that must both be set up:

| Component | What it is | Location |
|---|---|---|
| Evidence npm project | SvelteKit app with SQL+Markdown reports | `evidence/` subdirectory at repo root |
| Evidence Docker service | Dev server running `npm run dev` inside container | `docker-compose.yml` |

The container **mounts the Evidence npm project** and serves it. The `.md` report files are the source-controlled artifacts — they live on disk and are served hot-reload by the container.

### Evidence Project Scaffold — What `npx degit` Creates

After `npx degit evidence-dev/template evidence/`:

```
evidence/
├── package.json                    # Evidence + SvelteKit dependencies
├── evidence.plugins.yaml           # Connector registrations (modify for DuckDB)
├── sources/                        # Data source configs (created by you, not scaffold)
│   └── local_duckdb/
│       └── connection.yaml
└── pages/
    ├── index.md                    # Home page (modify)
    └── gold/
        └── orders-summary.md      # Report (create)
```

The scaffold creates a `pages/` directory with a sample `index.md`. You replace it and add your Gold layer reports. Do NOT modify `package.json` unless adding additional Evidence components.

### Evidence Report Format — `orders-summary.md`

Create `evidence/pages/gold/orders-summary.md` with this content:

```markdown
---
title: Gold Layer — Orders Summary
---

# Orders Summary

Pipeline output from the most recent run. Source: `gold.orders_mart`.

```sql orders_overview
select
  count(*)                                              as total_orders,
  sum(total_amount)                                     as total_revenue,
  sum(case when has_return then 1 else 0 end)           as total_returns,
  round(
    100.0 * sum(case when has_return then 1 else 0 end)
    / count(*), 1
  )                                                     as return_rate_pct
from gold.orders_mart
```

<BigValue data={orders_overview} value="total_orders" title="Total Orders" />
<BigValue data={orders_overview} value="total_revenue" title="Total Revenue ($)" fmt="$#,##0.00" />
<BigValue data={orders_overview} value="return_rate_pct" title="Return Rate (%)" />

```sql orders_by_category
select
  category,
  count(*)        as order_count,
  sum(total_amount) as revenue
from gold.orders_mart
group by category
order by revenue desc
```

<DataTable data={orders_by_category} />
```

Notes on the format:
- SQL blocks use named identifiers (e.g. `` ```sql orders_overview ```) — the name is referenced in components as `{orders_overview}`
- `BigValue`, `DataTable` are built-in Evidence components from `@evidence-dev/core-components`
- Table references use the **DuckDB schema name directly** (e.g. `gold.orders_mart`) — Evidence DuckDB connector queries the file directly; no source name prefix needed in SQL
- If Evidence shows "table not found", check schema name: dbt writes to `gold` schema by default (`+schema: gold` in `dbt_project.yml`)

### DuckDB Path Resolution — Critical Detail

The `filename` in `connection.yaml` is resolved **relative to the `sources/local_duckdb/` directory**:
- In development outside Docker: `../dev.duckdb` → `evidence/dev.duckdb` (one level up from sources dir, still inside evidence/)
- The Docker env var **overrides this entirely**: `EVIDENCE_SOURCE__local_duckdb__filename=/evidence-workspace/dev.duckdb` — absolute path inside container where the repo root is mounted

The env var format is: `EVIDENCE_SOURCE__[source_name]__[option_key]` (double underscore separators, case-sensitive).

**This means `connection.yaml` has the right shape but wrong path for Docker** — the env var fixes it. This is intentional and the recommended Evidence pattern for Docker deployments.

### Docker Image — Verify Before Committing

The story uses `evidencedev/devenv:latest` (from `github.com/evidence-dev/docker-devenv`). The current `docker-compose.yml` stub has `ghcr.io/evidence-dev/evidence:latest`.

Before finalising `docker-compose.yml`:
1. Pull and inspect both: `docker pull evidencedev/devenv:latest && docker pull ghcr.io/evidence-dev/evidence:latest`
2. Check their entrypoints: `docker inspect evidencedev/devenv:latest --format='{{.Config.Entrypoint}}'`
3. Use whichever runs `npm install && npm run dev` from the working directory

If `ghcr.io/evidence-dev/evidence:latest` does not run a dev server (it may be a production build image), switch to `evidencedev/devenv:latest`.

### Platform: `linux/amd64` for DuckDB

The DuckDB native Node.js bindings (`duckdb` npm package) has historically had `linux/arm64` support from v0.6+ but some Evidence connector versions pin older DuckDB builds. If the container fails to start with an architecture error:
- Set `platform: linux/amd64` (runs under Rosetta 2 on Apple Silicon)
- This is the same pattern already used for the `lightdash` service in `docker-compose.yml`

If `linux/arm64` works cleanly, prefer it (better native performance on Apple Silicon).

### ZScaler TLS (From Story 2.8/2.9 Learning)

`npx degit`, `npm install`, and any Evidence data source initialisation may make outbound HTTPS calls. On this machine, ZScaler intercepts TLS and requires the CA bundle at `~/.certs/cacert.pem`.

If any npm command fails with `SSLCertVerificationError` or `CERT_UNTRUSTED`:
```bash
source ~/.zshrc   # Loads REQUESTS_CA_BUNDLE, SSL_CERT_FILE, NODE_EXTRA_CA_CERTS
npx degit evidence-dev/template evidence/
```

The container's `npm install` also runs through ZScaler on first start. If the Evidence container fails to start with TLS errors in `docker compose logs evidence`, the fix is to configure `NODE_EXTRA_CA_CERTS` in the container environment pointing to the mounted CA bundle.

See `docs/troubleshooting-dbt-deps-zscaler-tls.md` for full details.

### Container Startup Time

On first `make start`, the Evidence container runs `npm install` which downloads ~200 MB of packages. Allow **60–120 seconds** before the dev server is ready at `http://localhost:18010`. Subsequent starts are fast (node_modules cached in the volume mount).

Note: because `node_modules` lives in `./evidence/node_modules/` on the host (via the volume mount), it persists between container restarts — `npm install` only re-runs if `package.json` changes.

### DuckDB Read Access — No Concurrency Issue

Evidence reads DuckDB concurrently with Elementary (`edr report`) and potentially other tools. DuckDB supports multiple concurrent readers — only concurrent writers are blocked. The pipeline sequence (dbt writes, then Evidence reads) is safe.

### Files NOT to Modify

- `models/` — no SQL model changes needed
- `dbt_project.yml` — no changes needed
- `Makefile` — `open-docs` already opens `http://localhost:18010`; `run-pipeline` does not need to trigger Evidence rebuild (Evidence hot-reloads from DuckDB on page load)
- `profiles.yml` — Evidence connects directly to DuckDB, not via dbt profiles
- `requirements.txt` — Evidence is Node.js based, not Python

### Scope Boundaries

| In scope | Out of scope |
|---|---|
| Scaffold Evidence npm project in `evidence/` | Adding Evidence to CI/CD |
| Configure DuckDB source and at least one Gold report | Adding multiple report pages (one is sufficient for AC) |
| Update docker-compose.yml Evidence service | MetricFlow integration (Story 2.7) |
| Add Evidence dirs to `.gitignore` | Evidence authentication / multi-user setup |
| End-to-end validation | Lightdash (Story 3.4) |

### Project Structure Notes

New files/directories created in this story:

| Path | Action | Notes |
|---|---|---|
| `evidence/` | Create (scaffold) | Evidence npm project root |
| `evidence/package.json` | Create (via degit) | Do not modify manually |
| `evidence/evidence.plugins.yaml` | Create/Modify | Add `@evidence-dev/duckdb` plugin |
| `evidence/sources/local_duckdb/connection.yaml` | Create | DuckDB source config |
| `evidence/pages/index.md` | Create/Replace | Home page |
| `evidence/pages/gold/orders-summary.md` | Create | Gold layer report |
| `docker-compose.yml` | Modify | Update Evidence service |
| `.gitignore` | Modify | Add Evidence build artifacts |

### References

- Evidence Docker image: `github.com/evidence-dev/docker-devenv`
- Evidence DuckDB connector docs: `docs.evidence.dev/core-concepts/data-sources/duckdb`
- Evidence report format: `docs.evidence.dev/core-concepts/queries`
- Port allocation: `architecture.md` § "Port Allocation" — Evidence=18010
- Makefile `open-docs` target: `Makefile` line 32–38 (already opens port 18010)
- ZScaler TLS fix: `docs/troubleshooting-dbt-deps-zscaler-tls.md`
- Gold layer schema: `dbt_project.yml` — `+schema: gold`
- Gold models: `models/gold/marts/orders_mart.sql`, `models/gold/facts/fct_orders.sql`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- 2026-04-08: Created isolated worktree branch `story/2-11-evidence-analytical-reports` from `origin/main` to avoid unrelated local changes on `story/2-12b-silver-incremental-idempotency-fix`.
- 2026-04-08: `make start` initially failed in the clean worktree because `dbt_packages/` were missing; resolved by running `dbt deps` in the worktree before re-running Docker validation.
- 2026-04-08: `make run-pipeline` exposed first-run dlt bootstrap issues for `faker_file` and `jsonplaceholder`; direct diagnostic dlt runs created the Bronze tables, after which the standard pipeline command succeeded end-to-end.
- 2026-04-08: The scaffolded Evidence template required Node 20+, and the older `evidencedev/devenv:latest` image plus env-var DuckDB override did not boot the app successfully; switched to a native `node:20-bookworm` dev container and a repo-root-relative DuckDB path in `connection.yaml`, then verified the service on port 18010.

### Completion Notes List

- Scaffolded the Evidence app with `npx degit`, kept the project under `evidence/`, and committed SQL+Markdown report pages for the pipeline home page and Gold-layer orders summary.
- Added a DuckDB-backed Evidence data source for the repo `dev.duckdb`, with the working connector path validated against the mounted Docker workspace and the report querying `gold.orders_mart`.
- Replaced the compose stub with a working Evidence dev service, validated `make start`, `make run-pipeline`, `/`, `/gold/orders-summary/`, `make open-docs`, and `PYTHONPATH=. pytest -q tests`.
- Added a focused regression test covering the Evidence scaffold, report files, DuckDB source config, and Docker service wiring.

### File List

- .gitignore
- docker-compose.yml
- tests/test_story_2_11_evidence.py
- evidence/package.json
- evidence/package-lock.json
- evidence/evidence.config.yaml
- evidence/evidence.plugins.yaml
- evidence/pages/index.md
- evidence/pages/gold/orders-summary.md
- evidence/sources/local_duckdb/connection.yaml
- evidence/sources/needful_things/connection.yaml
- evidence/.gitignore
- evidence/.npmrc
- evidence/README.md
- _bmad-output/implementation-artifacts/2-11-evidence-analytical-reports.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
