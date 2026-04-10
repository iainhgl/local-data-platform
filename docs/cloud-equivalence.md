# Cloud Equivalence

This platform is designed to teach portable data engineering patterns. Each local component has a close cloud or SaaS analogue so learners can map local practice to production tooling.

| Local Component | Cloud Equivalent | Pattern | Cloud migration notes |
|---|---|---|---|
| DuckDB | BigQuery Serverless / Redshift Serverless | Serverless analytics warehouse | Replace the local file with a managed warehouse and update the dbt profile target. |
| dlt | Fivetran / Airbyte | Managed ingestion and connector orchestration | Keep source contracts stable and move credentials plus schedules into the managed platform. |
| dbt Core | dbt Cloud | Transformation, testing, and documentation | Shift runs, docs jobs, and environment variables into dbt Cloud jobs and environments. |
| MinIO | Amazon S3 / GCS / Azure Blob | Object storage landing zone | Swap the endpoint and credentials for the target cloud bucket service. |
| Trino | Amazon Athena / BigQuery | SQL query federation and lakehouse compute | Point models and BI tools at the managed query layer and keep table formats consistent. |
| Airflow | Amazon MWAA / Cloud Composer (GCP) | Workflow orchestration | Promote DAGs and secrets into the managed Airflow control plane. |
| Keycloak | Amazon Cognito / Auth0 | Identity and access management | Recreate realms, clients, and roles using the destination provider's auth model. |
| Prometheus + Grafana | CloudWatch / Datadog | Metrics, dashboards, and alerting | Replace scrape targets with agent or managed integrations and port dashboards over. |
| Superset | Looker / Tableau | BI exploration and dashboards | Rebuild semantic layers and dashboards in the chosen BI service. |
| Elementary | Monte Carlo / Great Expectations Cloud | Data quality observability | Move test telemetry and incident workflows into the managed monitoring product. |
| Evidence | Observable / Hex | Analytical storytelling and reports | Recreate report pages as notebooks, apps, or hosted analytical docs. |
| OpenMetadata | Google Dataplex / Microsoft Purview | Catalog, lineage, and metadata governance | Migrate metadata ingestion and stewardship workflows into the enterprise catalog. |

## Why this mapping matters

The local stack keeps the concepts visible and inspectable. When teams later move to cloud services, they are mostly swapping platform implementations rather than relearning the core ingestion, transformation, governance, and observability patterns.
