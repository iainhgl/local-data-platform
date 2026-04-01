{{ config(
    unique_key="_dlt_id",
    incremental_strategy="delete+insert"
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'returns') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > COALESCE((SELECT MAX(_dlt_load_id) FROM {{ this }}), '')
    {% endif %}
),

failed AS (
    SELECT
        return_id,
        order_id,
        product_id,
        return_date,
        reason,
        refund_amount,
        created_at,
        _dlt_load_id,
        _dlt_id,
        'faker_returns_file' AS _source,
        CASE
            WHEN _dlt_id IS NULL THEN 'missing _dlt_id'
            WHEN return_id IS NULL THEN 'missing return_id'
            WHEN order_id IS NULL THEN 'missing order_id'
            WHEN product_id IS NULL THEN 'missing product_id'
            WHEN refund_amount IS NULL THEN 'missing refund_amount'
            WHEN refund_amount <= 0 THEN 'non-positive refund_amount'
        END AS _failed_reason,
        CURRENT_TIMESTAMP AS _failed_at
    FROM source_data
    WHERE
        _dlt_id IS NULL
        OR return_id IS NULL
        OR order_id IS NULL
        OR product_id IS NULL
        OR refund_amount IS NULL
        OR refund_amount <= 0
)

SELECT *
FROM failed
