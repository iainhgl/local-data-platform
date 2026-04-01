{{ config(
    unique_key="_dlt_id",
    incremental_strategy="delete+insert"
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'customers') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > COALESCE((SELECT MAX(_dlt_load_id) FROM {{ this }}), '')
    {% endif %}
),

failed AS (
    SELECT
        customer_id,
        first_name,
        last_name,
        email,
        phone,
        address,
        city,
        country,
        created_at,
        _dlt_load_id,
        _dlt_id,
        'faker_customers_file' AS _source,
        CASE
            WHEN _dlt_id IS NULL THEN 'missing _dlt_id'
            WHEN customer_id IS NULL THEN 'missing customer_id'
            WHEN email IS NULL THEN 'missing email'
        END AS _failed_reason,
        CURRENT_TIMESTAMP AS _failed_at
    FROM source_data
    WHERE
        _dlt_id IS NULL
        OR customer_id IS NULL
        OR email IS NULL
)

SELECT *
FROM failed
