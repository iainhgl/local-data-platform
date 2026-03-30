---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
workflowComplete: true
completedAt: '2026-03-25'
inputDocuments: ['_bmad-output/brainstorming/brainstorming-session-2026-03-24-1200.md']
workflowType: 'prd'
brainstormingCount: 1
briefCount: 0
researchCount: 0
projectDocsCount: 0
classification:
  projectType: developer_tool
  domain: data_engineering_education
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - local-data-platform

**Author:** Iain
**Date:** 2026-03-25

## Executive Summary

A portable, local-first data engineering reference template that delivers a realistic end-to-end pipeline in a single `make start` command. Built for data engineers who already understand the basics and want hands-on experience with the full modern data stack — ingestion, transformation, quality, observability, and serving — running together as an integrated system on their laptop.

The primary goal is community activation: giving engineers within a team something concrete to run, break, tweak, and learn from. The value is in the doing — watching data move through Medallion layers, triggering pipeline failures, replaying bad records, switching a query engine — not in reading documentation about how those things work.

### What Makes This Special

Most learning resources teach components in isolation. This template wires everything together: dbt sits at the centre, surrounded by realistic ingestion (dlt), orchestration (cron → Airflow), access and serving (Lightdash, Evidence, Superset, MetricFlow), observability (Elementary, Prometheus, Grafana), governance (role-based access, PII masking, dbt contracts), and optionally an open lakehouse (MinIO + Iceberg + Trino). The realism is the pedagogy — a system realistic enough that the patterns learned here transfer directly to production.

Five deployment profiles provide progressive complexity: `simple` (DuckDB + dbt + cron) through to `full` (Airflow + OpenMetadata + Prometheus + Grafana + Keycloak + MCP Server + Superset). A Makefile interface removes all command friction. AI readiness is built into the architecture from the start — not retrofitted — via a semantic layer (MetricFlow) exposed as an MCP-protocol tool, positioning the template ahead of most enterprise data platforms today.

## Project Classification

- **Project Type:** Developer Tool — portable reference framework/template
- **Domain:** Data Engineering Education
- **Complexity:** Medium — multi-technology orchestration, no regulatory constraints
- **Project Context:** Greenfield

## Success Criteria

### User Success

An engineer clones the repository, runs `make start` on the `simple` profile, and has a working end-to-end pipeline within minutes. Success is getting it running — data moving from source through Bronze/Silver/Gold, dbt models executing, results queryable via Lightdash or Evidence. No prior setup beyond Docker required.

### Business Success

The template is shared in the internal community and generates feedback — questions, observations, or conversations about the architecture or tool choices. Feedback of any kind signals the material is engaging engineers and prompting learning.

### Technical Success

- All v1 deployment profiles (`simple`, `postgres`, `lakehouse`, `full`) run end-to-end without manual intervention beyond `make start`
- Pipeline is idempotent — re-running produces identical output
- Jaffle Shop and Faker synthetic data both work within the `simple` profile
- `make help` documents all available commands
- dbt tests pass on all profiles on a clean run

### Measurable Outcomes

- Time-to-running: engineer reaches a working `simple` pipeline in under 10 minutes from clone
- Feedback received from at least one community member after sharing
- All five profiles start cleanly on a standard developer laptop (16GB RAM, Docker Desktop)

## User Journeys

### Journey 1: The Curious Learner — First Run

**Persona:** Priya, mid-level data engineer. She's worked with dbt at her company but has only ever seen one part of the stack at a time — her team's Airflow setup, or their Redshift warehouse, never the full picture end-to-end.

**Opening Scene:** A colleague posts the repository link in the data engineering community channel. Priya clones it on her laptop during a quiet afternoon, half-expecting it to be another README-heavy project that takes an hour to configure.

**Rising Action:** She runs `make help`, scans the commands, runs `make start`. Docker pulls images, services start. A few minutes later she runs `make run-pipeline` — dbt executes, Elementary logs test results, Lightdash is available in her browser. She can see Jaffle Shop orders flowing through Bronze → Silver → Gold. She runs `make open-docs` and sees the full dbt DAG.

**Climax:** She clicks through to the Elementary dashboard and sees test pass/fail rates across the models. She's used dbt tests before but never seen them displayed as a live observability layer alongside the data. Something clicks — quality and pipeline are the same thing, not separate concerns.

**Resolution:** Priya spends another 30 minutes exploring. She posts a question in the community channel about how the Bronze layer is structured. The conversation starts.

---

### Journey 2: The Tinkerer — Breaking and Learning

**Persona:** Marcus, senior data engineer. He ran the `simple` profile last week and wants to understand what happens under the hood.

**Opening Scene:** Marcus switches to the `lakehouse` profile. He's curious about the Trino + Iceberg combination — he's heard about it but never run it locally.

**Rising Action:** The profile starts. He runs the pipeline successfully once. Then he edits a dbt model, introduces a type mismatch between a staging model and a mart, and reruns. The dbt test fails. He reads the error, traces it through the DAG in `make open-docs`, finds the model, fixes it. Reruns. Green.

**Climax:** He then disables the source freshness check in `sources.yml`, runs stale data through, and watches what Elementary flags. He didn't expect the freshness warning to surface as a visible signal in the dashboard alongside test failures. He now understands why freshness is a first-class quality concern, not just a config option.

**Resolution:** Marcus posts in the community: "The Trino profile is worth running just to see what query/storage separation actually looks like in practice."

---

### Journey 3: The Community Sharer — Dropping It and Fielding Questions

**Persona:** Iain, sharing the template in his company's internal data engineering community.

**Opening Scene:** Iain posts the repository link: "Built this as a local data engineering playground — one `make start` to get a full pipeline running. Simple profile for starters, lakehouse if you want to go deeper. Feedback welcome."

**Rising Action:** A few engineers clone it. One hits a Docker memory issue on an 8GB RAM machine. Another asks why DuckDB is used instead of Postgres for the simple profile. A third wants to know if it works on Windows with WSL2.

**Climax:** The questions reveal real gaps — the README needs a hardware requirements note, the DuckDB choice needs a one-line rationale, and WSL2 compatibility needs a test. Iain patches the README and re-shares.

**Resolution:** Three engineers have run the `simple` profile. One has reached `lakehouse`. The conversation is active. The template has done its job.

---

### Journey Requirements Summary

| Capability | Revealed By |
|---|---|
| `make start` / `make help` working on first clone, zero config | All journeys |
| Clear hardware requirements documented upfront | Journey 3 |
| DuckDB and profile choices briefly explained in README | Journey 3 |
| dbt DAG + Elementary dashboard accessible via `make open-docs` | Journey 1, 2 |
| Pipeline errors surface clearly enough to be debugged independently | Journey 2 |
| Profile switching documented and testable | Journey 2, 3 |
| WSL2 / cross-platform compatibility documented | Journey 3 |

## Domain-Specific Requirements

### Technical Constraints

**Platform Compatibility**
- Primary: macOS ARM (Apple Silicon, M-series). All Docker images must have `linux/arm64` variants — any image without ARM64 support blocks the profile on the primary target platform.
- Secondary: Linux x86_64.
- WSL2 (Windows): documented as supported but not a primary target; compatibility notes in README.

**Resource Requirements**
- Minimum: 8GB RAM — sufficient for `simple` and `postgres` profiles.
- Recommended: 16GB RAM for `lakehouse` and `full` profiles (Airflow, OpenMetadata, Keycloak, Trino, Prometheus/Grafana, Superset/Redis/Celery stack combined).
- Resource requirements per profile documented in README and surfaced in `make help` output.

**Version Strategy**
- All services use `latest` tag — no version pinning in `docker-compose.yml` or `requirements.txt`.
- Documentation notes that `latest` is intentional for this learning context; production deployments should pin all versions with a tested compatibility matrix.
- dbt adapter versions (dbt-duckdb, dbt-postgres, dbt-trino) also unpinned; compatibility notes included in docs.

**Port Allocation**
- Services assigned ports from a high base (e.g. 18000+), incrementing by 10 per service.
- Full port map documented in README and `docker-compose.yml` comments.

### Risk Mitigations

| Risk | Mitigation |
|---|---|
| Docker image lacks ARM64 variant | Validate `linux/arm64` support before including a service in a profile |
| Tool ecosystem changes break the template | Document update procedure; `latest` tag means users always get current versions |
| Full profile exceeds available RAM on 16GB machines | Document memory allocation per service; provide profile-level resource guidance |
| dbt adapter / engine version incompatibility | Test each profile's adapter/engine combination; document tested environment |

### Out of Scope

Corporate proxy configuration, VPN compatibility, and firewall rules are the learner's responsibility.

## Innovation & Novel Patterns

### Detected Innovation Areas

**1. MCP Server as First-Class Data Product Interface**

The template exposes the semantic layer (MetricFlow) as an MCP-protocol tool, making the data product natively queryable by AI agents alongside Lightdash, Evidence, and Superset. This is an architectural primitive, not a retrofit. Most enterprise data platforms treat AI access as an add-on; this template treats the AI agent as a peer consumer of the same semantic layer human analysts use — subject to the same role-based access controls (Invariant 14). The MCP server demonstrates that a well-governed, well-documented data product is already AI-ready by construction.

**2. schema.yml as Dual-Purpose Infrastructure**

`schema.yml` is simultaneously the governance artifact (column descriptions, PII tags, data types, ownership, test definitions) and the AI interface specification (machine-readable context that determines AI agent answer quality). Documentation investment compounds: every column description written for governance directly improves AI query accuracy. This reframes documentation from maintenance overhead to infrastructure.

**3. The 16 Architectural Invariants as a Teaching Paradigm**

Rather than teaching tools, the template teaches the principles that survive tool changes. Each configuration decision is traceable to a named invariant. When a learner asks "why does this use merge instead of insert?" the answer is Invariant 11 (idempotency). This makes the template teachable at multiple levels of depth and coherent as the tool landscape evolves.

### Market Context

The MCP protocol (launched late 2024) is early. Native MCP integration in local data engineering tooling is effectively non-existent at time of writing. Positioning MCP as a core interface reflects where the data + AI stack is heading: from "data product consumed by dashboards" to "data product consumed by agents and dashboards equally."

### Validation Approach

- MCP server queryable by Claude against the Faker dataset using natural language — correct answers grounded in MetricFlow metric definitions
- AI agent queries subject to the same RBAC as human queries — `analyst_role` cannot see PII columns via MCP
- Semantic layer rejects queries for undefined metrics — no hallucinated joins against raw Bronze tables

### Risk Mitigation

| Risk | Mitigation |
|---|---|
| MCP protocol evolves rapidly | Track MCP spec changes; document the version implemented |
| LLM query quality depends on schema.yml completeness | Provide fully-populated `schema.yml` template as reference |
| Learners skip the semantic layer and query raw tables | Document why this produces wrong answers (Invariant 13); demonstrate the contrast |

## Developer Tool Specific Requirements

### Project-Type Overview

A Docker Compose-based local data engineering framework. The primary interface is the Makefile (environment lifecycle and common workflows) plus the dbt CLI (direct model execution, testing, documentation). Learners interact as engineers — reading config files, running CLI commands, inspecting outputs directly.

### Language Matrix

| Language / Format | Role |
|---|---|
| Python | dlt ingestion scripts, Faker data generator, dbt artifacts parsing, Elementary |
| SQL | dbt models (Bronze, Silver, Gold/Marts) |
| YAML | dbt project config, `schema.yml`, Docker Compose profiles, source definitions |
| Makefile | Learner-facing command interface — wraps Docker Compose lifecycle and dbt workflows |
| Jinja | dbt macro templating within SQL models |
| HCL | Terraform scaffold (stretch goal, `full` profile only) |

### Installation Methods

- **Primary:** `git clone` + `make start`. No local Python install required for standard profiles.
- **Secondary:** `pip install -r requirements.txt` for running dlt scripts or the Faker generator outside containers.
- **dbt packages:** `dbt deps` (wrapped as `make install`) installs dbt-expectations and Elementary from `packages.yml`.
- Not published to any registry — cloned template, not an installed library.

### Interface Surface

**Makefile:**

| Command | Purpose |
|---|---|
| `make start` | Start all services for the active profile |
| `make stop` | Stop all services |
| `make run-pipeline` | Execute full pipeline (ingestion → dbt run → dbt test) |
| `make open-docs` | Open dbt docs and Elementary dashboard in browser |
| `make help` | Print all available commands with descriptions |

**dbt CLI (direct, expected for learners):** `dbt run`, `dbt test`, `dbt docs generate`, `dbt docs serve`, `dbt source freshness`. The Makefile wraps these for convenience but does not replace them.

**MCP server:** Exposes MetricFlow semantic layer as MCP-protocol tool. Documented connection instructions included.

### Sample Data

| Dataset | Profile | Purpose |
|---|---|---|
| Jaffle Shop | `simple` (onboarding) | dbt canonical example — zero cognitive overhead |
| Faker synthetic e-commerce | All (default) | Orders, customers, products, returns. Two sources: DB + API. Configurable volume |
| NYC Taxi (TLC) | Advanced track | Real, messy, multi-year — forces schema evolution handling |

### Open Table Format Reference

The `lakehouse` profile uses Apache Iceberg as the default open table format. Delta Lake and Hudi are documented as alternatives — not implemented, but compared in a reference table covering write performance, streaming/upsert support, and ecosystem alignment (Spark, Trino, cloud warehouse compatibility). Provides context for the Iceberg default and awareness of the broader landscape.

### Migration Guide (Cloud Equivalence)

| Local Component | Cloud Equivalent |
|---|---|
| DuckDB | Snowflake, BigQuery, Redshift |
| MinIO | AWS S3, GCS, Azure Blob |
| Iceberg (local) | Iceberg on S3 / Snowflake Iceberg tables |
| Trino | Athena, Starburst, Trino on EMR |
| Local Airflow | MWAA, Cloud Composer, Astronomer |
| Keycloak | Okta, Azure AD, Google Workspace |
| Prometheus + Grafana | Datadog, Grafana Cloud, CloudWatch |
| Superset | Tableau, PowerBI, Looker |

### Implementation Considerations

- All profile-specific configuration driven by `.env` — one variable change switches the active backend. `profiles.yml` reads env vars across all environments.
- IDE-agnostic. dbt Power User (VS Code extension) is a useful companion but not required. No `.vscode/` settings committed.
- ARM64 compatibility required for all Docker images.
- Port allocation: high base (18000+), incrementing by 10 per service, fully documented.
- Superset (`full` profile) requires Redis and Celery workers alongside the main container, plus an init container to bootstrap the database and admin user.

**WSL2 (Windows) — documented but untested:** Expected to work with Docker Desktop (WSL2 backend) but unverified. Pre-testing requirements: (1) `.gitattributes` enforcing LF line endings — prevents Makefile/shell script CRLF breakage; (2) clone into WSL2 filesystem (`~/`), not Windows filesystem (`/mnt/c/...`) — Docker volume mounts from the Windows FS are slow and permission-prone; (3) WSL2 memory cap (default 50% RAM or 8GB) may require `.wslconfig` adjustment for `full` profile. Document all three in README. Mark as community-verified once a Windows user confirms.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**Approach:** Experience MVP — get learners hands-on with a complete, working pipeline as fast as possible. The `simple` profile proves the concept: one command, a working end-to-end pipeline, observable results. Community sharing happens at this point while subsequent profiles are built in parallel.

**Resource:** Solo project. Each profile is a self-contained epic picked up immediately after the previous one is stable.

**Foundational investment:** The `simple` profile builds shared infrastructure (`.env`, `profiles.yml`, Makefile, `schema.yml` template, Faker generator, dbt project structure) that all subsequent profiles inherit. Each additional profile is additive, not a rebuild.

### Phase 1 — MVP (`simple` profile)

**User Journeys:** Journey 1 (Curious Learner), Journey 3 (Community Sharer)

- `simple` profile: DuckDB + dbt + cron + Lightdash + Evidence + Elementary
- Jaffle Shop onboarding data + Faker synthetic e-commerce generator
- Makefile interface: `make start`, `make stop`, `make run-pipeline`, `make open-docs`, `make help`
- Fully populated `schema.yml` template
- Bronze / Silver / Gold Medallion layer structure
- dbt tests + dbt-expectations + Elementary observability dashboard
- README: hardware requirements, quick-start, profile overview, cloud equivalence table, WSL2 notes
- ARM64 validated for all `simple` profile images

### Phase 2 — Fast Follow-On (`postgres` + `lakehouse` profiles)

Highest priority after MVP — this is where the majority of learning value is realised.

- `postgres` profile: Postgres + dbt + cron + Lightdash + Evidence + Elementary. Teaches server warehouse, SQL clients, RBAC.
- `lakehouse` profile: MinIO + Iceberg + Trino + dbt + cron + Lightdash + OpenMetadata. Teaches open table format, query/storage separation, cross-system lineage. Includes Iceberg vs Delta Lake vs Hudi reference.
- `lakehouse-spark` profile: MinIO + Iceberg + Spark + dbt. Teaches batch processing patterns.
- NYC Taxi dataset (advanced track) introduced with `lakehouse` profile.

### Phase 3 — Full Profile (`full`)

- Airflow + OpenMetadata + Prometheus + Grafana + Loki + Keycloak + MCP Server + Superset — layered onto any prior profile backend
- dbt contracts enforced on serving layer (marts only)
- PII tagging, column-level masking, row-level access control
- Three-role RBAC: `engineer_role`, `analyst_role`, `pii_analyst_role`
- MCP server exposing MetricFlow semantic layer as AI agent interface
- Pipeline alerting as first-class configuration (errors, quality failures, freshness SLA breaches)
- Terraform scaffold (`terraform/` directory, commented-out stretch goal)

**Out of Scope (v1):** Streaming/CDC (Debezium + Redpanda), Dagster orchestration variant, TPC-DS benchmarking module. Spark lakehouse documented in comparison table only.

### Risk Mitigation

| Risk | Mitigation |
|---|---|
| ARM64 image unavailable for a service | Validate before committing to a profile; document exceptions |
| MCP protocol instability | Isolate as discrete component; profile works without it if MCP is broken |
| Full profile exceeds 16GB RAM | Profile-level resource docs; Keycloak/observability stack selectively disableable |
| Superset init complexity | Init container pattern handles bootstrap; documented in README |
| Low community engagement | Share after `simple` profile is stable — don't wait for full v1 |
| Solo resource constraint | Phased epics — Phase 2 delivers most learning value if Phase 3 is delayed |

## Functional Requirements

### Environment & Profile Management

- **FR1:** Learner can start a complete profile environment with a single command
- **FR2:** Learner can stop all profile services with a single command
- **FR3:** Learner can switch between deployment profiles via configuration without modifying pipeline code
- **FR4:** Learner can view all available commands and their descriptions via a help command
- **FR5:** Learner can execute the complete pipeline (ingestion → transformation → testing) with a single command
- **FR6:** Learner can open documentation and observability dashboards in a browser with a single command
- **FR7:** The system executes pipeline runs on a defined schedule (cron-based in `simple` profile, workflow-scheduled in `full` profile)

### Data Ingestion

- **FR8:** The system ingests data from file sources into the Bronze layer
- **FR9:** The system ingests data from a REST API source into the Bronze layer
- **FR10:** Learner can generate synthetic e-commerce data at configurable volume for use as pipeline input
- **FR11:** The system appends raw data to the Bronze layer without modification or deletion — the Bronze layer is immutable
- **FR12:** The system records ingestion metadata (source, run ID, timestamp) on every raw record

### Data Transformation

- **FR13:** Learner can execute dbt models across Bronze, Silver, and Gold layers
- **FR14:** Learner can execute individual dbt models or model subsets by selector, tag, or path
- **FR15:** The system structures all data through a Medallion architecture (Bronze → Silver → Gold)
- **FR16:** The system executes transformations idempotently — re-running produces identical output with no duplicates
- **FR17:** The system captures failed records with sufficient context to diagnose and replay them

### Data Quality & Observability

- **FR18:** Learner can view dbt test results (pass/fail) per model after each pipeline run
- **FR19:** The system monitors source data freshness against declared SLAs and surfaces breaches
- **FR20:** Learner can view an observability dashboard showing test pass rates, anomalies, freshness status, and schema changes
- **FR21:** The system tracks and displays row counts and storage sizes per Medallion layer per pipeline run
- **FR22:** Learner can trace a failed test to the specific model and column in the DAG
- **FR23:** The system detects and surfaces schema changes across pipeline runs

### Data Access & Serving

- **FR24:** Learner can explore data and metrics via a dbt-native BI interface
- **FR25:** Learner can view code-driven, version-controlled analytical reports
- **FR26:** Learner can explore data via a traditional drag-and-drop BI dashboard interface (full profile)
- **FR27:** Learner can query data directly via SQL using a standard client connection
- **FR28:** The system exposes metrics and dimensions via a semantic layer with consistent, unambiguous business definitions
- **FR29:** Learner can view the full dbt transformation DAG showing model dependencies and column lineage
- **FR30:** The system provides cross-system data lineage from source through ingestion, transformation, and serving (full profile)

### Access Control & Governance

- **FR31:** The system enforces role-based access control across three roles: `engineer_role`, `analyst_role`, and `pii_analyst_role`
- **FR32:** The `analyst_role` receives PII columns masked by default; the `pii_analyst_role` receives unmasked access via explicit grant only
- **FR33:** The system logs every access to unmasked PII data
- **FR34:** Learner can declare column descriptions, data types, PII tags, ownership, and test definitions in a single configuration artifact
- **FR35:** The system enforces schema contracts on serving layer models, rejecting downstream consumption if the contract is violated
- **FR36:** The system provides a data catalog with cross-system lineage and PII column classification (full profile)
- **FR37:** The system authenticates all human and service-to-service access — no unauthenticated queries reach the data layer
- **FR38:** The full profile provides local enterprise SSO simulation via an identity provider, with documented mapping to cloud IdP equivalents

### AI Agent Access

- **FR39:** An AI agent can query business metrics and dimensions via the semantic layer using natural language
- **FR40:** AI agent access is subject to the same role-based access controls as human analyst access
- **FR41:** The semantic layer prevents AI agents from querying raw tables directly — all queries route through defined metrics and dimensions
- **FR42:** Learner can connect an MCP-compatible AI client to the data product's MCP server using documented connection instructions

### Alerting

- **FR43:** The system notifies a declared recipient when pipeline execution fails, quality tests breach thresholds, or source freshness SLAs are missed
- **FR44:** Alert configuration is declared alongside pipeline and data contracts — not wired to a specific tool's UI — so alerting survives tool changes

### Documentation & Discoverability

- **FR45:** Learner can generate and serve dbt documentation showing model descriptions, column lineage, and test coverage
- **FR46:** The system provides a cloud equivalence mapping table documenting the production equivalent of each local component
- **FR47:** The system provides an open table format comparison reference (Iceberg, Delta Lake, Hudi) covering write performance, streaming support, and ecosystem alignment
- **FR48:** The README documents hardware requirements, quick-start instructions, profile descriptions, and WSL2 compatibility notes
- **FR49:** The system documents port allocations for all services in both the README and compose configuration

## Non-Functional Requirements

### Performance

- **NFR1:** The `simple` profile reaches a running state within 5 minutes on minimum hardware, after initial Docker image pull
- **NFR2:** A full pipeline run (ingestion → dbt run → dbt test) on Jaffle Shop completes within 2 minutes on the `simple` profile
- **NFR3:** dbt docs generation and serve completes within 30 seconds for the default dataset
- **NFR4:** Lightdash and Evidence dashboards respond to initial page load within 10 seconds of pipeline completion
- **NFR5:** The Faker data generator produces up to 100,000 rows within 60 seconds on minimum hardware

### Security

- **NFR6:** No credentials, secrets, or API keys are committed to the repository — all sensitive configuration stored in `.env` files excluded by `.gitignore`
- **NFR7:** The repository ships with a `.env.example` file containing placeholder values only, documenting all required environment variables
- **NFR8:** PII columns in the Faker dataset are masked for `analyst_role` by default — unmasked access requires explicit grant and is logged
- **NFR9:** Service-to-service authentication uses local credentials via `.env`; the README documents the equivalent IAM role pattern for cloud deployments

### Integration

- **NFR10:** All Docker Compose configuration uses Docker Compose v2 syntax (`docker compose`, not `docker-compose`)
- **NFR11:** All Docker images provide `linux/arm64` variants — images without ARM64 support are explicitly documented as known exceptions
- **NFR12:** Each profile's dbt adapter version is tested against the declared query engine version; tested combinations are documented
- **NFR13:** The MCP server conforms to the MCP protocol specification version in use at implementation; the version is documented
- **NFR14:** The serving layer exposes a standard SQL interface (JDBC/ODBC-compatible) enabling connection from any standard BI client without template modification

### Reliability

- **NFR15:** Every profile starts cleanly from a fresh Docker state (`docker compose down -v` + `make start`) without manual intervention
- **NFR16:** The pipeline is fully idempotent — running `make run-pipeline` twice produces identical row counts and test results
- **NFR17:** dbt tests pass on a clean run for all profiles using default sample data
- **NFR18:** The `simple` profile functions correctly on 8GB RAM; the `full` profile is documented as requiring 16GB RAM

### Maintainability

- **NFR19:** Each deployment profile is independently startable — modifying one profile does not break others
- **NFR20:** All profile-specific configuration is isolated to `.env` and `docker-compose.yml` — dbt models, ingestion scripts, and `schema.yml` are shared across profiles and contain no profile-specific logic
- **NFR21:** The Makefile is self-documenting — `make help` lists and describes every available target without requiring the user to read the Makefile source
