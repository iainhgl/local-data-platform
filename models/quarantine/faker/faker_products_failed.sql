{{ config(
    unique_key="_dlt_id",
    incremental_strategy="delete+insert"
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'products') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > COALESCE((SELECT MAX(_dlt_load_id) FROM {{ this }}), '')
    {% endif %}
),

failed AS (
    SELECT
        product_id,
        product_name,
        category,
        unit_price,
        sku,
        created_at,
        _dlt_load_id,
        _dlt_id,
        'faker_products_file' AS _source,
        CASE
            WHEN _dlt_id IS NULL THEN 'missing _dlt_id'
            WHEN product_id IS NULL THEN 'missing product_id'
            WHEN product_name IS NULL THEN 'missing product_name'
            WHEN unit_price IS NULL THEN 'missing unit_price'
            WHEN unit_price <= 0 THEN 'non-positive unit_price'
        END AS _failed_reason,
        CURRENT_TIMESTAMP AS _failed_at
    FROM source_data
    WHERE
        _dlt_id IS NULL
        OR product_id IS NULL
        OR product_name IS NULL
        OR unit_price IS NULL
        OR unit_price <= 0
)

SELECT *
FROM failed
