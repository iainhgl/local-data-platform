{{ config(
    unique_key="_dlt_id",
    incremental_strategy="delete+insert"
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'orders') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > COALESCE((SELECT MAX(_dlt_load_id) FROM {{ this }}), '')
    {% endif %}
),

failed AS (
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
        _dlt_load_id,
        _dlt_id,
        CASE
            WHEN _dlt_id IS NULL THEN 'missing _dlt_id'
            WHEN order_id IS NULL THEN 'missing order_id'
            WHEN customer_id IS NULL THEN 'missing customer_id'
            WHEN product_id IS NULL THEN 'missing product_id'
            WHEN quantity IS NULL THEN 'missing quantity'
            WHEN quantity <= 0 THEN 'non-positive quantity'
            WHEN total_amount IS NULL THEN 'missing total_amount'
            WHEN total_amount <= 0 THEN 'non-positive total_amount'
        END AS _failed_reason,
        'faker_orders_file' AS _source,
        CURRENT_TIMESTAMP AS _failed_at
    FROM source_data
    WHERE
        _dlt_id IS NULL
        OR order_id IS NULL
        OR customer_id IS NULL
        OR product_id IS NULL
        OR quantity IS NULL
        OR quantity <= 0
        OR total_amount IS NULL
        OR total_amount <= 0
)

SELECT *
FROM failed
