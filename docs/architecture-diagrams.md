# Architecture Diagrams — test-data-product

**Date:** 2026-03-25
**Status:** Reference — input to implementation phase

---

## About These Diagrams

These diagrams represent the **target architecture** of the data engineering template in a technology-agnostic form. They are intended as implementation guidance — describing *what each component must do* rather than *which tool does it*. The specific tools (DuckDB, Postgres, Trino, Airflow, dlt, etc.) are deployment decisions that vary by profile; the architectural roles shown here remain constant across all profiles.

### How to Read the Invariant Labels

Each component is annotated with one or more **architectural invariants** — the durable principles that survive any tool change. These emerged from the project's First Principles analysis and are referenced throughout the architecture document. Format: `[Inv.N: short description]`.

The full set of 16 invariants is documented in `_bmad-output/brainstorming/brainstorming-session-2026-03-24-1200.md`.

### Diagram Set

| # | Diagram | Type | Shows |
|---|---|---|---|
| 1 | System Context | C4-L1 | External actors and the system boundary |
| 2a | Data Path | C4-L2 | Core data flow components and their invariant roles |
| 2b | Operational Layer | C4-L2 | Orchestration, governance, observability, and lineage |
| 3 | Ingestion Flow | Sequence | Raw data moving from source to immutable storage |
| 4 | Transformation Flow | Sequence | Bronze → Silver → Gold with quality gates and quarantine |
| 5 | Query Flow | Sequence | Human analyst and AI agent consuming data via semantic layer |
| 6 | Error & Replay Flow | Sequence | Diagnosing failures in quarantine and replaying corrected records |

---

## Diagram 1 — System Context (C4 Level 1)

Shows the system and the external actors that interact with it. At this level, the internal structure is a black box.

```mermaid
C4Context
    title System Context — Data Engineering Reference Template

    Person(learner, "Data Engineer / Learner", "Runs, breaks, and learns from a complete local pipeline")
    Person(analyst, "Data Analyst", "Explores and queries data products via BI tools")
    Person_Ext(ai_agent, "AI Agent", "Queries business metrics via natural language over MCP protocol")

    System(template, "Data Engineering Template", "Local-first portable reference implementation. Teaches ingestion, transformation, quality, governance, and serving as an integrated system.")

    System_Ext(file_sources, "File Data Sources", "CSV, JSON files used as raw pipeline input")
    System_Ext(api_sources, "API Data Sources", "REST APIs providing operational or transactional data")
    System_Ext(idp, "Identity Provider", "Authenticates all human and service identities before data access")

    Rel(learner, template, "Operates via CLI / Makefile")
    Rel(analyst, template, "Queries via BI interface")
    Rel(ai_agent, template, "Queries via MCP protocol")
    Rel(file_sources, template, "Provides raw data")
    Rel(api_sources, template, "Provides raw data")
    Rel(template, idp, "Verifies all identities against")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## Diagram 2a — Data Path (C4 Level 2)

The core data flow — from raw source data through to governed, served data products. Components are named by their architectural role. The specific storage engine or transformation tool is a deployment detail that varies by profile; the responsibilities shown here are invariant.

```mermaid
C4Container
    title Container Diagram — Data Path (Tech-Agnostic)

    Person(analyst, "Data Analyst", "Queries data products via BI tools")
    Person_Ext(ai_agent, "AI Agent", "Queries via MCP protocol")
    System_Ext(sources, "Data Sources", "Files and APIs providing raw data")

    System_Boundary(template, "Data Engineering Template — Data Path") {
        Container(ingestion, "Ingestion Layer", "Data Movement", "Moves raw data from source to storage without modification or loss. [Inv.1: every pipeline has source, destination, mechanism]")
        Container(bronze, "Raw Storage", "Immutable Store", "Append-only record of everything received and when. Never modified or deleted. [Inv.8: raw data is immutable and always replayable]")
        Container(transformation, "Transformation Engine", "Business Logic", "Applies cleaning, deduplication, and business rules across Medallion layers. [Inv.11: pipeline is idempotent]")
        Container(quarantine, "Quarantine Store", "Failure Record", "Captures every failed record with reason and context for diagnosis and replay. [Inv.9: every failure produces a queryable record]")
        Container(silver, "Clean Storage", "Validated Data", "Quality-tested, deduplicated data with transformation-time metadata stamps.")
        Container(gold, "Serving Storage", "Governed Data Products", "Business-ready data with enforced schema contracts and stable interfaces. [Inv.6: governance survives a tool swap]")
        Container(semantic, "Semantic Layer", "Metric Contract", "Single source of truth for metric and dimension definitions. Mandatory interface for all consumers. [Inv.13: semantic layer is the AI contract]")
        Container(bi_interface, "BI Interface", "Human Query Layer", "Exploration and reporting via standard SQL interface. [Inv.16: enterprise BI connects via standard interfaces]")
        Container(mcp_interface, "AI Access Interface", "MCP Protocol", "Exposes semantic layer to AI agents as a structured tool. [Inv.14: AI consumers subject to same access controls as humans]")
    }

    Rel(sources, ingestion, "Raw data")
    Rel(ingestion, bronze, "Append-only writes")
    Rel(bronze, transformation, "Read raw")
    Rel(transformation, silver, "Write clean records")
    Rel(transformation, quarantine, "Write failed records")
    Rel(silver, transformation, "Read clean")
    Rel(transformation, gold, "Write governed marts")
    Rel(gold, semantic, "Metrics defined against")
    Rel(semantic, bi_interface, "Serve metrics")
    Rel(semantic, mcp_interface, "Expose as tool")
    Rel(bi_interface, analyst, "Query results")
    Rel(mcp_interface, ai_agent, "Grounded answers")
```

---

## Diagram 2b — Operational Layer (C4 Level 2)

The cross-cutting operational concerns — orchestration, governance, observability, and lineage. These components wrap and support the data path without sitting in it. Shown separately to avoid diagram clutter and because their implementation scope varies significantly by deployment profile.

```mermaid
C4Container
    title Container Diagram — Operational Layer (Tech-Agnostic)

    Person(learner, "Data Engineer / Learner", "Operates and monitors the pipeline via CLI")
    System_Ext(data_path, "Data Path", "Ingestion, transformation, and serving containers (see Data Path diagram)")
    System_Ext(idp, "Identity Provider", "Authenticates all human and service identities")

    System_Boundary(ops, "Data Engineering Template — Operational Layer") {
        Container(orchestration, "Orchestrator", "Pipeline Scheduler", "Sequences, schedules, and monitors pipeline execution. Alerting declared as a pipeline contract — not wired to a tool. [Inv.10: alerting is a contract, not a feature]")
        Container(governance, "Governance Layer", "Access Control", "Enforces role-based access and PII masking at the data layer — not the interface layer. Role truth declared once and consumed everywhere. [Inv.4: enforce at the data] [Inv.5: single source of role truth]")
        Container(observability, "Observability Layer", "Pipeline Health", "Tracks test pass rates, data freshness, anomalies, schema changes, and layer-level row counts and sizes. [Inv.12: data discoverable by humans and machines]")
        Container(catalog, "Catalog & Lineage", "Discoverability", "Cross-system lineage from source through to serving. Machine-readable metadata context for AI agents. [Inv.15: context quality determines AI answer quality]")
    }

    Rel(learner, orchestration, "Operates via Makefile / CLI")
    Rel(orchestration, data_path, "Trigger ingestion and transformation runs")
    Rel(orchestration, observability, "Report run results")
    Rel(governance, data_path, "Enforce RBAC and PII masking")
    Rel(governance, idp, "Verify all identities against")
    Rel(observability, data_path, "Monitor quality, freshness, and lineage")
    Rel(catalog, data_path, "Ingest lineage artefacts from transformation runs")
    Rel(learner, observability, "Monitor pipeline health and data quality")
```

---

## Diagram 3 — Ingestion Flow (Sequence)

How raw data moves from its source into immutable storage. The ingestion layer is responsible for transport and metadata stamping only — no transformation, no filtering, no business logic.

```mermaid
sequenceDiagram
    participant SRC as Data Source
    participant ORCH as Orchestrator
    participant ING as Ingestion Layer
    participant BRZ as Raw Storage (Bronze)
    participant OBS as Observability Layer

    ORCH->>ING: Trigger ingestion run
    ING->>SRC: Request data (file read / API call)
    SRC-->>ING: Raw records
    ING->>ING: Stamp metadata (load_id, source, ingested_at)
    ING->>BRZ: Append raw records
    BRZ-->>ING: Write confirmed
    ING-->>ORCH: Run complete — n records loaded
    ORCH->>OBS: Log run results (record count, load_id, duration)

    Note over BRZ: Append-only — records never modified or deleted after write<br/>Full history always replayable from this layer (Inv.8)
    Note over ING: Metadata stamps make every batch traceable<br/>load_id links raw records to their ingestion run
```

---

## Diagram 4 — Transformation Flow (Sequence)

How raw data is promoted through the Medallion layers. The transformation engine runs in two passes — Bronze → Silver (clean and validate), then Silver → Gold (aggregate and govern). Quality gates operate at each layer boundary.

```mermaid
sequenceDiagram
    participant ORCH as Orchestrator
    participant TRANS as Transformation Engine
    participant BRZ as Raw Storage (Bronze)
    participant SLV as Clean Storage (Silver)
    participant QRN as Quarantine Store
    participant GLD as Serving Storage (Gold)
    participant OBS as Observability Layer
    participant ALRT as Alert System

    ORCH->>TRANS: Trigger transformation run

    Note over TRANS,SLV: Silver Pass — Clean and validate
    TRANS->>BRZ: Read raw records (incremental by load_id)
    BRZ-->>TRANS: Raw records
    TRANS->>TRANS: Apply cleaning rules and business logic
    TRANS->>SLV: Write clean records (idempotent merge)
    TRANS->>QRN: Write failed records + failure reason + timestamp
    TRANS->>OBS: Run quality tests against Silver
    OBS-->>TRANS: Test results (pass / fail per model)

    Note over TRANS,GLD: Gold Pass — Aggregate and govern
    TRANS->>SLV: Read clean records
    SLV-->>TRANS: Clean records
    TRANS->>TRANS: Apply business logic and aggregations
    TRANS->>GLD: Write mart models (schema contract enforced)
    TRANS->>OBS: Run quality tests against Gold
    OBS-->>TRANS: Test results

    OBS->>OBS: Update layer metrics (row counts, sizes, freshness)

    opt Quality tests fail or freshness SLA breached
        OBS->>ALRT: Raise alert
        ALRT-->>ORCH: Notification dispatched
    end

    TRANS-->>ORCH: Pipeline run complete

    Note over SLV,QRN: Clean and failed records produced in same run — partial success is possible (Inv.9)
    Note over GLD: Contract enforcement — stable interface regardless of upstream changes (Inv.6)
    Note over TRANS: Re-running produces identical output — no duplicates, no side effects (Inv.11)
```

---

## Diagram 5 — Query Flow (Sequence)

How human analysts and AI agents consume data. Both routes pass through the semantic layer and are subject to identical role-based access controls — raw tables are never exposed directly to either consumer type.

```mermaid
sequenceDiagram
    participant H as Human Analyst
    participant AI as AI Agent
    participant IDP as Identity Provider
    participant BI as BI Interface
    participant MCP as AI Access Interface (MCP)
    participant SEM as Semantic Layer
    participant GOV as Governance Layer
    participant GLD as Serving Storage (Gold)

    Note over H,AI: All consumers authenticated before any data access (Inv.3)

    par Human query flow
        H->>IDP: Authenticate
        IDP-->>H: Identity confirmed → analyst_role
        H->>BI: Request metric or explore data
        BI->>SEM: Resolve metric definition
        SEM->>GOV: Check role permissions
        GOV-->>SEM: Permitted — PII columns masked for analyst_role
        SEM->>GLD: Execute query against governed mart
        GLD-->>SEM: Results (PII masked)
        SEM-->>BI: Metric results
        BI-->>H: Visualisation / report
    and AI agent query flow
        AI->>IDP: Authenticate (service identity)
        IDP-->>AI: Identity confirmed → analyst_role
        AI->>MCP: Natural language query
        MCP->>SEM: Resolve to metric and dimension definitions
        SEM->>GOV: Check role permissions
        GOV-->>SEM: Permitted — PII columns masked
        SEM->>GLD: Execute query against governed mart
        GLD-->>SEM: Results (PII masked)
        SEM-->>MCP: Structured results grounded in metric definitions
        MCP-->>AI: Answer
    end

    Note over SEM: Raw tables never exposed to either consumer<br/>All queries route through defined metrics and dimensions (Inv.13)
    Note over GOV: AI agent carries analyst_role — identical RBAC as human analyst<br/>No elevated service account access (Inv.14)
    Note over MCP: Undocumented metrics cannot be queried<br/>Semantic layer rejects undefined requests — no hallucinated joins (Inv.15)
```

---

## Diagram 6 — Error & Replay Flow (Sequence)

What happens when records fail transformation. The quarantine store makes failures a first-class, queryable output rather than a silent discard. The immutability of raw storage means replay is always safe — the same Bronze input always produces the same output.

```mermaid
sequenceDiagram
    participant ENG as Data Engineer
    participant OBS as Observability Layer
    participant QRN as Quarantine Store
    participant TRANS as Transformation Engine
    participant BRZ as Raw Storage (Bronze)
    participant SLV as Clean Storage (Silver)

    Note over QRN: A prior pipeline run completed with failures — n records written to quarantine

    ENG->>OBS: Check pipeline health dashboard
    OBS-->>ENG: Failed records flagged — quarantine.orders_failed contains n records

    ENG->>QRN: Query failed records
    QRN-->>ENG: Records returned with _failed_reason, original payload, _failed_at, load_id

    ENG->>ENG: Diagnose root cause

    alt Root cause: transformation logic error
        ENG->>TRANS: Fix transformation rule in Silver model
        TRANS->>BRZ: Re-read full raw history for affected source
        BRZ-->>TRANS: Full raw records (immutable — unchanged since original ingestion)
        TRANS->>SLV: Write corrected clean records (idempotent merge)
        TRANS->>QRN: Re-run — previously failed records now pass, quarantine cleared
    else Root cause: bad source data
        Note over BRZ: Bronze is read-only — bad source records remain as permanent audit trail<br/>They cannot be deleted or modified (Inv.8)
        ENG->>TRANS: Apply corrective logic at Silver transformation level
        TRANS->>SLV: Write corrected records (idempotent merge)
        TRANS->>QRN: Re-run — corrected records now pass, quarantine cleared
    end

    TRANS->>OBS: Run quality tests on replayed records
    OBS-->>ENG: Tests pass — quarantine empty for affected models

    Note over BRZ: Immutability enables replay — same Bronze input always produces same output<br/>Re-run is safe because the pipeline is idempotent (Inv.8 + Inv.11)
    Note over QRN: Quarantine is a queryable audit trail, not a dead-letter queue<br/>Every failure is diagnosable, replayable, and resolvable (Inv.9)
```

---

*Generated: 2026-03-25 | Source: `_bmad-output/planning-artifacts/architecture.md`*
