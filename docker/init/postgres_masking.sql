-- Story 3.2: Postgres PII masking and access logging.
-- Run after dbt materializes tables. Re-run on every pipeline execution to handle table recreation by dbt.

CREATE TABLE IF NOT EXISTS public.pii_access_log (
    id          SERIAL PRIMARY KEY,
    logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    role_name   TEXT        NOT NULL,
    schema_name TEXT        NOT NULL,
    table_name  TEXT        NOT NULL,
    query_text  TEXT
);

GRANT INSERT, SELECT ON public.pii_access_log TO pii_analyst_role;
GRANT USAGE, SELECT ON SEQUENCE public.pii_access_log_id_seq TO pii_analyst_role;

ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_line_prefix = '%t [%p]: user=%u,db=%d ';
SELECT pg_reload_conf();

REVOKE SELECT ON silver.faker_customers FROM analyst_role;
CREATE OR REPLACE VIEW silver.faker_customers_masked AS
SELECT
    customer_id,
    '***REDACTED***'::varchar AS first_name,
    '***REDACTED***'::varchar AS last_name,
    '***REDACTED***'::varchar AS email,
    '***REDACTED***'::varchar AS phone,
    '***REDACTED***'::varchar AS address,
    city,
    country,
    created_at,
    _dlt_load_id,
    _dlt_id,
    _source,
    _loaded_at
FROM silver.faker_customers;
GRANT SELECT ON silver.faker_customers_masked TO analyst_role;

REVOKE SELECT ON gold.dim_customers FROM analyst_role;
CREATE OR REPLACE VIEW gold.dim_customers_masked AS
SELECT
    customer_id,
    '***REDACTED***'::varchar AS first_name,
    '***REDACTED***'::varchar AS last_name,
    '***REDACTED***'::varchar AS email,
    '***REDACTED***'::varchar AS phone,
    '***REDACTED***'::varchar AS address,
    city,
    country,
    created_at,
    _dlt_load_id,
    _dlt_id,
    _source,
    _loaded_at
FROM gold.dim_customers;
GRANT SELECT ON gold.dim_customers_masked TO analyst_role;

REVOKE SELECT ON gold.orders_mart FROM analyst_role;
CREATE OR REPLACE VIEW gold.orders_mart_masked AS
SELECT
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    total_amount,
    status,
    created_at,
    has_return,
    return_id,
    return_date,
    return_reason,
    refund_amount,
    '***REDACTED***'::varchar AS first_name,
    '***REDACTED***'::varchar AS last_name,
    '***REDACTED***'::varchar AS email,
    city,
    country,
    product_name,
    category,
    sku,
    _dlt_load_id,
    _source,
    _loaded_at
FROM gold.orders_mart;
GRANT SELECT ON gold.orders_mart_masked TO analyst_role;

REVOKE SELECT ON quarantine.faker_customers_failed FROM analyst_role;
CREATE OR REPLACE VIEW quarantine.faker_customers_failed_masked AS
SELECT
    customer_id,
    '***REDACTED***'::varchar AS first_name,
    '***REDACTED***'::varchar AS last_name,
    '***REDACTED***'::varchar AS email,
    '***REDACTED***'::varchar AS phone,
    '***REDACTED***'::varchar AS address,
    city,
    country,
    created_at,
    _dlt_load_id,
    _dlt_id,
    _failed_reason,
    _source,
    _failed_at
FROM quarantine.faker_customers_failed;
GRANT SELECT ON quarantine.faker_customers_failed_masked TO analyst_role;
