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
