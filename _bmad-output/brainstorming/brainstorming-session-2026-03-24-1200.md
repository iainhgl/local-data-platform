---
stepsCompleted: [1, 2, 3, 4]
session_active: false
workflow_completed: true
ideas_generated: 42
inputDocuments: []
session_topic: 'Portable template data product for learning data engineering concepts'
session_goals: 'Tech options evaluation (pros/cons) + tech-agnostic C4/sequence architecture that survives stack changes'
selected_approach: 'ai-recommended'
techniques_used: ['Morphological Analysis', 'First Principles Thinking']
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Iain
**Date:** 2026-03-24

---

## Session Overview

**Topic:** Portable template data product for learning data engineering concepts — ingestion, physical/logical modelling, ELT pipelines, query/access patterns, technology choices
**Goals:** Evaluate technology options with pros/cons; define a tech-agnostic reference architecture (C4-style + sequence diagrams) that survives tech stack changes

**Constraints:** Local-first (Docker/Compose), cloud-portable, dbt-centric, one backend per deployment, exercises list deferred to later phase

---

## Technique Selection

**Approach:** AI-Recommended Techniques

**Recommended Techniques:**
- **Morphological Analysis:** Map all parameter axes with all candidate options — produces the full tech option space
- **First Principles Thinking:** Strip away tool names to expose architectural invariants — produces the durable tech-agnostic skeleton
- **Six Thinking Hats:** Skipped — pros/cons covered organically during Morphological Analysis

**AI Rationale:** Analytically complex, multi-dimensional problem. User is technically fluent, wants structured outputs. Sequence: divergent mapping → principled design → convergent evaluation.

---

## Technique Execution: Morphological Analysis

### Axis 1: Storage & Query Engine

**Sub-layer 1a — Physical Storage:**

| Option | Profile | Notes |
|---|---|---|
| DuckDB file | simple / default | Zero-server, in-process, columnar — local Snowflake proxy |
| Postgres | postgres | Server-based, cloud-portable, familiar to all engineers |
| MinIO (S3-compatible) | lakehouse | Object storage for Parquet/Iceberg files |
| Snowflake | cloud | Cloud-native warehouse target |

**Sub-layer 1b — Table Format:**

| Option | Status | Notes |
|---|---|---|
| None (native) | simple/postgres profiles | Format internal to engine |
| Apache Iceberg | lakehouse profiles (default) | Open, ACID, time travel, engine-agnostic, ecosystem momentum |
| Delta Lake | documented only | Strong Azure/Databricks ecosystem, delta-rs for local tooling |
| Apache Hudi | documented only | Streaming/upsert optimised, Uber-originated |

**Decision:** Iceberg as implementation default. Delta Lake and Hudi documented with comparison table (write performance, streaming support, ecosystem alignment).

**Sub-layer 1c — Query/Compute Engine:**

| Option | Profile | Notes |
|---|---|---|
| DuckDB | simple | Embedded, analytical, mirrors Snowflake SQL dialect |
| Postgres | postgres | OLTP+OLAP, row-level security, well-known |
| Trino | lakehouse | Federated query engine — pure query, no processing. dbt-trino adapter |
| Spark | lakehouse-spark | Batch processing engine — compute+query unified. dbt-spark adapter |
| Snowflake | cloud | Managed cloud warehouse |

**Key architectural distinction:** In simple/postgres profiles, storage and query engine are unified. In lakehouse profiles they split — Trino is a pure query layer over files (teaches "decouple compute from query"). Spark unifies processing and query (teaches "heavy compute" patterns). Both can share the same Iceberg tables on MinIO — this is the full open lakehouse story.

**Lakehouse variants:**
- **Trino + Iceberg + MinIO** — federated query lakehouse. Best for: analytics, SQL federation
- **Spark + Iceberg + MinIO** — batch processing lakehouse. Best for: large-scale transforms, ML pipelines
- **Spark + Trino + Iceberg + MinIO** — full open lakehouse. Spark writes, Trino reads same Iceberg tables

---

### Axis 2: Orchestration / Scheduler

| Option | Profile | Notes |
|---|---|---|
| cron + shell | simple (default) | Zero infra baseline. Teaches the concept without framework overhead. Pedagogically valuable as the "before" state |
| Apache Airflow | full / cloud default | Industry standard. MWAA (AWS), Cloud Composer (GCP), Astronomer (managed). Most transferable enterprise skill |
| Dagster | follow-on learning | Asset-oriented paradigm, first-class dbt integration, Dagster+ hybrid cloud model. Not yet enterprise-mainstream but directionally correct |
| Prefect | documented | Modern Python-native, lighter than Airflow, hybrid execution |

**Decision:** cron for simple profile (local), Airflow for full profile and cloud default. Dagster documented as follow-on learning track — teaches asset-oriented paradigm that Airflow 3.x and dbt Cloud are converging toward. Not positioned as a local Airflow substitute.

**Airflow managed services note:** MWAA, Cloud Composer, and Astronomer provide enterprise-procurement-ready managed Airflow. Dagster+ exists (hybrid model — control plane managed, execution in your VPC) but no hyperscaler-native equivalent yet.

---

### Axis 3: Ingestion Mechanisms

| Option | Profile | Notes |
|---|---|---|
| dlt (data load tool) | All (default) | Python library, zero server, schema inference, supports REST APIs + files + databases. Code-first alternative to managed connectors. Fast enterprise adoption |
| Simple file drop | simple (baseline) | Python script + watched folder. Teaches what ingestion *is* before introducing tools |
| Airbyte | documented | UI-driven connector platform (300+ connectors). Runs locally via Docker. Teaches "connector catalogue" mental model (Fivetran/Stitch equivalent) |
| Debezium + Redpanda | follow-on / documented | CDC via Kafka-compatible streaming. Redpanda replaces Kafka locally (same API, much lighter). Full CDC pattern documented but not a deployment profile |

**Decision:** dlt as default ingestion tool for file + API patterns. Streaming/CDC documented as a separate follow-on learning project — it breaks the dbt batch model and warrants its own treatment.

---

### Axis 4: Access & Serving Layer

| Option | Profile | Notes |
|---|---|---|
| Lightdash | All (default) | dbt-native BI — reads schema.yml directly. Metrics/dimensions defined in dbt become the Lightdash data model. No business logic duplication |
| dbt Semantic Layer (MetricFlow) | All | Built into dbt Core 1.6+. Single metric definition consumed by all downstream tools. The "single source of truth for numbers" |
| Evidence | All | SQL + Markdown code-driven reports. Version-controlled alongside dbt models. Zero server (static site) |
| Apache Superset | full | Traditional drag-and-drop dashboard builder. Connects via SQLAlchemy. The open-source Tableau equivalent for analysts |
| JDBC/ODBC docs | documented | Connection pattern for Tableau, PowerBI, Qlik. Architecture guarantees the standard interface; the tools plug in |
| OpenMetadata | All | Data catalog + cross-system lineage hub. Ingests dbt manifest, Airbyte metadata, database schemas — stitches end-to-end lineage |
| MCP Server | full | Wraps semantic layer as MCP-protocol tool for AI agent access. Direct integration with Claude and other MCP-compatible agents |
| dbt Semantic Layer API | full | Programmatic access for AI agents — query business concepts, not raw tables |

---

### Axis 5: Lineage, Observability & Governance

**Lineage:**

| Component | Notes |
|---|---|
| dbt docs (native) | Table-level DAG lineage. `dbt docs generate` + serve. First-class output, always current |
| OpenMetadata | Cross-system lineage. Source → ingestion → transformation → serving. Ingests dbt manifest.json + catalog.json |
| Column-level lineage | Parsed from compiled dbt SQL via sqllineage / OpenMetadata column-level parser |

**Data Quality:**

| Component | Profile | Notes |
|---|---|---|
| dbt tests + dbt-expectations | All | Built-in (unique, not_null, accepted_values, relationships) + 50+ extended tests. Quality as part of the pipeline |
| Elementary | All | dbt package — anomaly detection, schema change monitoring, freshness, HTML observability dashboard. Zero additional infra |
| Data freshness (sources.yml) | All | SLA declared in config. Warns/errors if source data is stale. Time dimension of quality |

**Observability:**

| Component | Profile | Notes |
|---|---|---|
| dbt artifacts → metrics | All | run_results.json parsed post-run → row counts, model timing, test results pushed to Prometheus or warehouse metrics table |
| Layer size metrics | All | Bronze/Silver/Gold row counts + storage sizes tracked per run. Makes transformation value tangible |
| Elementary dashboard | All | Data health view: test pass/fail rates, anomalies, freshness, schema changes |
| Prometheus + Grafana | full | Infrastructure + pipeline metrics. Docker footprint ~300MB |
| Grafana Loki + Promtail | full | Log aggregation from all containers. Correlated with metrics by timestamp |
| Unified ops dashboard | full | Single Grafana dashboard: pipeline status + infra health + data freshness + layer sizes |

**Governance:**

| Component | Notes |
|---|---|
| schema.yml as governance artifact | Fully populated: column descriptions, data types, tags (pii: true), ownership, test definitions. The data dictionary |
| dbt contracts (dbt 1.5+) | `contract: enforced: true` on marts/serving layer models only. Raw/staging contract-free. Teaches interface enforcement without blocking learner experimentation |
| PII tagging + column classification | dbt meta/tags → OpenMetadata surfaces classification → access control policies reference tags |
| Row/column-level access control | Postgres RLS + column masking. Trino access control. Same table shows different data to different roles |

**AuthN/AuthZ:**

Three roles throughout all profiles:
- `engineer_role` — pipeline admin, full access, schema changes
- `analyst_role` — query access, PII columns masked by default
- `pii_analyst_role` — PII columns unmasked, requires explicit grant + audit logging on every PII access

Service-to-service auth: `.env` credentials locally, documented as IAM roles in cloud (no passwords — identity is the compute resource).

Human auth:
- Simple/postgres/lakehouse profiles: per-tool local credentials
- Full profile: **Keycloak** container — local enterprise SSO simulation (OIDC/SAML). Documented mapping to Okta/Azure AD/Google Workspace for cloud

---

### Axis 6: Deployment Model

**Docker Compose Profiles:**

| Profile | Core Services | Learning Focus |
|---|---|---|
| `simple` | DuckDB + dbt + cron + Lightdash + Evidence + Elementary | Core ELT, modelling, basic access, data quality |
| `postgres` | Postgres + dbt + cron + Lightdash + Evidence + Elementary | Server warehouse, SQL clients, RBAC |
| `lakehouse` | MinIO + Iceberg + Trino + dbt + cron + Lightdash + OpenMetadata | Open table format, query/storage separation, lineage |
| `lakehouse-spark` | MinIO + Iceberg + Spark + dbt + cron + Lightdash | Batch processing, heavy compute lakehouse |
| `full` | Any above + Airflow + OpenMetadata + Prometheus + Grafana + Loki + Keycloak + MCP Server | Orchestration, governance, observability, SSO, AI access |

**Supporting infrastructure:**
- `.env`-driven configuration — one line to switch backends. Same profiles.yml reads env vars across all environments
- **Makefile as learner interface** — `make start-simple`, `make run-pipeline`, `make open-docs`, `make help`. Removes "what command do I run?" friction
- Cloud equivalence documented as a mapping table (DuckDB→Snowflake, MinIO→S3, local Airflow→MWAA etc.) — not a Terraform deployment but a concrete upgrade guide
- Terraform scaffold in `terraform/` as commented-out stretch goal

---

### Axis 7: Sample Data & Domain

| Dataset | Profile | Purpose |
|---|---|---|
| Jaffle Shop | simple (onboarding) | dbt's canonical example. Zero cognitive overhead. Gets learners to a working pipeline in minutes |
| Faker synthetic e-commerce | All (default) | Orders, customers, products, returns. Two sources: transactional DB + product catalogue API. Configurable volume (100 rows → 1M). Self-contained, no download |
| NYC Taxi (TLC trip data) | advanced track | Real, messy, multi-year. Format changes across years force schema evolution handling. Natural time partitioning |
| TPC-DS | benchmarking track | Industry-standard warehouse benchmark. 24 fact tables, multiple subject areas. Enables stack comparison (DuckDB vs Trino vs Snowflake on identical queries) |

**Synthetic data generator** included as a Python script (Faker) — generates realistic data on each pipeline run, simulating a live system growing over time.

---

### Axis 8: Data Visualisation

**Locally runnable:**

| Tool | Profile | Enterprise Equivalent | Notes |
|---|---|---|---|
| Lightdash | All | Looker / dbt Cloud Explore | dbt-native metric exploration |
| Evidence | All | Tableau + Git (aspirational) | Code-driven reports, version-controlled |
| Superset | full | Tableau / PowerBI | Traditional drag-and-drop dashboards |

**Enterprise BI (documented connection pattern only):** Tableau, PowerBI, Qlik connect via JDBC/ODBC. The architecture guarantees a standard SQL interface — the tools plug in without modification. PowerBI Desktop is Windows-only and not Docker-friendly; Tableau Desktop is licensed. Teaching the *connection pattern* is more valuable than trying to run them locally.

---

## Technique Execution: First Principles Thinking

### The 16 Architectural Invariants

These are the things that remain true regardless of which tools are in the stack. Every component in the C4 diagrams implements one or more of these invariants. Tool names are interchangeable; these guarantees are not.

#### Topology

**Invariant 1: Data Movement Has Source, Destination, and Mechanism**
Data always travels from origin (operational system, API, file) to analytical destination. Three components always exist regardless of tooling. The mechanism (dlt, Airbyte, Kafka) changes — the topology doesn't. This is the fundamental architectural shape of every data pipeline ever built.

#### Governance

**Invariant 2: Access Is Role-Governed, Not Tool-Governed**
The right to see data is a property of the data and the consumer's role — not a feature of whichever query engine sits in front of it. Any compliant implementation enforces this regardless of whether access comes via Trino, Postgres, Lightdash, or a REST API. Access control logic cannot live only in the tool.

**Invariant 5: A Single Source of Role Truth Must Exist**
The mapping of "person X has role Y" cannot be defined independently in each tool. It must be declared once — in an IdP or central role registry — and all tools must defer to it. Distributed role management is ungovernable at scale. This is why enterprise platforms converge on SSO + SCIM provisioning.

**Invariant 6: The Governance Model Must Survive a Tool Swap**
If access control is implemented only in tool-specific configurations, swapping that tool means rebuilding governance from scratch. The durable layer is the role + policy declaration (schema.yml tags, catalog policy, warehouse RBAC). Tools are plugged into that declaration. Architectural test: could you replace Lightdash with Superset tomorrow without changing who can see what?

**Invariant 14: AI Consumers Are Subject to the Same Access Controls as Human Consumers**
An AI agent querying data has an identity, a role, and a set of permissions — exactly like a human analyst. An agent with `analyst_role` cannot see PII. The most commonly missed governance gap in AI data applications: teams wire AI tools to a full-access service account, bypassing every control. This invariant closes that gap at the architecture level.

#### Security

**Invariant 3: Every Access Requires a Verified Identity First**
No data moves, no query executes, without the system first answering "who is asking?" Authentication is a prerequisite gate — a requirement of every interaction, not a feature of specific tools. The architecture must have an answer to: what happens when an identity is revoked or compromised?

**Invariant 4: Enforce at the Data, Not the Interface**
Enforcing access only in the BI tool or API layer is not real security — it's a UI lock on an open door. The warehouse/query engine must be the authoritative enforcement point. If a user with a direct SQL connection can bypass the BI tool and see PII, the governance model has failed regardless of what Lightdash shows.

#### Compliance

**Invariant 7: Sensitive Data Is Masked by Default, Visible by Exception**
The default state of PII is masked. Seeing it requires an explicit role grant — a positive grant to a named role, not a request to unblock. Every access to unmasked PII is logged. The burden of proof is on visibility, not on masking. Inverts the typical assumption ("visible unless restricted") to the production-correct assumption ("restricted unless granted").

#### Reliability

**Invariant 8: Raw Data Is Immutable and Always Replayable**
The Bronze layer is append-only and never modified or deleted. It is the source of truth for "what did we receive and when." Any downstream layer can be rebuilt from Bronze at any time. The pipeline is a pure function: same Bronze input always produces the same output. This is why the Medallion architecture exists — not aesthetic convention but a reliability guarantee.

**Invariant 9: Every Failure Produces a Record, Every Record Enables Replay**
When data fails validation, transformation, or loading, it is written to an error/quarantine table with full context (what failed, why, original payload, timestamp, run ID). Replay means reprocessing that specific record from raw after root cause is fixed. The error table is a first-class pipeline output — observable, queryable, actionable. Partial success becomes possible.

**Invariant 11: The Pipeline Is Idempotent**
Running the pipeline twice produces the same result as running it once. Re-processing Bronze always yields the same Silver and Gold output. No duplicate records, no double-counting, no side effects from re-runs. This is a design requirement, not an implementation detail — enforced via merge/upsert over insert, deterministic keys, run-ID stamping on every record.

#### Observability

**Invariant 10: Alerting Is a Contract, Not a Feature**
The data product must notify a defined recipient when something fails — pipeline errors, quality test failures, freshness SLA breaches. This notification contract is declared alongside the data contracts, not wired into a specific tool's UI. Alerting that lives only in Airflow's email config is lost when you swap schedulers. Alerting declared as a pipeline property survives tool changes.

#### Accessibility

**Invariant 12: Data Must Be Discoverable by Both Humans and Machines**
Every description, metric definition, relationship, and lineage record must be accessible programmatically — not just via a UI. A data product discoverable only by browsing a catalog UI is not AI-consumable. This invariant retroactively justifies every documentation decision — fully populated schema.yml, dbt docs, OpenMetadata are the machine-readable context layer AI agents need.

#### AI Readiness

**Invariant 13: The Semantic Layer Is the AI Contract**
AI agents must not query raw tables directly — they must query through a semantic layer that defines metrics, dimensions, grain, and business rules unambiguously. An LLM querying raw Bronze tables produces confidently wrong answers. MetricFlow is the mandatory interface for AI consumption, not just a convenience for consistent metrics.

**Invariant 15: Context Quality Determines AI Answer Quality**
An AI agent's ability to correctly query and interpret a data product is directly proportional to the quality of the semantic descriptions attached to it. Undocumented tables produce hallucinated queries. Well-described metrics with clear grain, filters, and business rules produce reliable answers. Documentation is not metadata — it is the AI's interface specification.

#### Portability

**Invariant 16: Enterprise BI Tools Connect via Standard Interfaces, Not Custom Integrations**
Tableau, PowerBI, Qlik, Looker — all connect via JDBC/ODBC or vendor-specific connectors. The serving layer must expose a standard SQL interface. If it does, any enterprise BI tool connects without modification. The architecture doesn't need to include Tableau — it needs to guarantee the interface Tableau requires.

---

## Idea Organisation and Prioritisation

### Thematic Organisation

**Theme 1: Stack Architecture** — Technology parameter map with clear defaults and alternatives at every axis
**Theme 2: Governance, Security & Compliance** — Role-based access, PII handling, contracts, identity
**Theme 3: Reliability & Operations** — Idempotency, error handling, replay, observability, alerting
**Theme 4: AI Readiness** — Semantic layer, MCP server, context quality, AI consumer access controls
**Theme 5: Learning Design & Deployment** — Progressive complexity profiles, sample data tiering, Makefile interface

### Breakthrough Concepts

1. **MCP Server as AI agent interface** — wraps the semantic layer as an MCP-protocol tool. Makes the data product natively queryable by current-generation AI agents. Positions the template ahead of most enterprise data platforms today.

2. **Medallion layers as observability anchors** — Bronze/Silver/Gold row counts and sizes tracked per run create automatic data quality storytelling. Watching data shrink from raw → clean → aggregated is the most visceral demonstration of what transformation *does*.

3. **dbt contracts on serving layer only** — enforced on marts and serving models, contract-free on raw/staging. Teaches the "stable published interface" concept without blocking learner experimentation in development layers.

4. **Keycloak for local SSO simulation** — the most commonly skipped topic in data engineering tutorials. Runs in Docker. Gives learners the real enterprise SSO pattern before they encounter it in production.

5. **schema.yml as dual-purpose artifact** — simultaneously the governance document (column descriptions, PII tags, ownership) and the AI context injection (machine-readable descriptions for LLM prompts and semantic layer). Documentation investment compounds over time.

### Quick Wins (Highest value, lowest complexity)

1. **Jaffle Shop + simple profile** — learners productive in under 10 minutes, zero friction
2. **Fully populated schema.yml template** — doubles as governance artifact and AI context
3. **dbt artifacts → layer metrics** — zero additional infra, immediate observability value from existing dbt output
4. **Makefile learner interface** — removes all "what command do I run?" friction with `make help`

### Prioritised Next Steps

**Priority 1 — Architecture Phase (immediate):**
- Produce C4 context, container, and component diagrams grounded in the 16 invariants
- Produce sequence diagrams for: ingestion flow, transformation run, error/replay flow, AI agent query flow
- Define the tech-agnostic component responsibilities (not tool names — layer names)

**Priority 2 — PRD Phase:**
- Formalise deployment profiles as product requirements
- Define the sample data strategy (Jaffle Shop → Faker → NYC Taxi progression)
- Specify the three roles and their access policies as functional requirements
- Define observability requirements (what metrics, what alert thresholds)

**Priority 3 — Implementation Phase:**
- Start with `simple` profile end-to-end (DuckDB + dbt + cron + Lightdash + Elementary)
- Jaffle Shop first, then Faker e-commerce
- Add profiles incrementally: postgres → lakehouse → full
- MCP server and Keycloak as final additions to full profile

**Follow-on learning tracks (out of scope for v1):**
- Streaming/CDC with Debezium + Redpanda
- Dagster as asset-oriented orchestration alternative
- Spark lakehouse variant
- TPC-DS benchmarking module

---

## Session Summary

### Key Achievements

- Complete technology parameter map across 8 axes — storage, table format, query engine, orchestration, ingestion, access/serving, governance/observability, deployment
- 16 tech-agnostic architectural invariants — the skeleton that survives any stack change, organised across Topology, Governance, Security, Compliance, Reliability, Observability, Accessibility, AI Readiness, and Portability concerns
- Clear scope boundaries — what runs locally, what is documented-only, what is a follow-on track
- Progressive deployment profile structure — `simple` → `postgres` → `lakehouse` → `lakehouse-spark` → `full`
- AI readiness built into the core architecture — not a retrofit

### Session Reflections

The most important insight from this session: the 16 invariants are not just abstract principles — they are the direct justification for every tool choice and configuration decision in the template. When a learner asks "why does this use merge instead of insert?" or "why is schema.yml so thoroughly documented?", the answer is an invariant, not a preference. This makes the template teachable at multiple levels of depth.

The AI readiness layer (Invariants 12-15, MCP server, semantic layer as AI contract) emerged organically from first principles rather than being bolted on. This suggests it is architecturally correct — not a trend feature but a natural consequence of building a well-governed, well-documented data product.

### Creative Facilitation Narrative

The session moved unusually quickly from divergent (Morphological Analysis) to principled (First Principles) without needing a formal convergence step. The Morphological Analysis was thorough enough that Six Thinking Hats would have repeated rather than added — a sign that the exploration reached genuine completeness. The 16 invariants emerged directly from the decisions already made, confirming the parameter map was internally consistent. The AI readiness section was the standout breakthrough — reframing documentation as infrastructure and schema.yml as an AI interface specification rather than metadata.

---

*Session document generated: 2026-03-24*
*Next recommended workflow: `bmad-bmm-create-prd` — use this document as input context*
