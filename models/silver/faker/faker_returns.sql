{{ config(
    unique_key="return_id",
    incremental_strategy="delete+insert"
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'returns') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY return_id ORDER BY _dlt_load_id DESC
        ) AS _row_num
    FROM source_data
),

final AS (
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
        CURRENT_TIMESTAMP AS _loaded_at
    FROM deduplicated
    WHERE _row_num = 1
)

SELECT *
FROM final
