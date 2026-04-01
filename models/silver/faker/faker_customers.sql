{{ config(
    unique_key="customer_id",
    incremental_strategy="delete+insert"
) }}

WITH source_data AS (
    SELECT *
    FROM {{ source('faker_file', 'customers') }}
    {% if is_incremental() %}
    WHERE _dlt_load_id > (SELECT MAX(_dlt_load_id) FROM {{ this }})
    {% endif %}
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id ORDER BY _dlt_load_id DESC
        ) AS _row_num
    FROM source_data
),

final AS (
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
        CURRENT_TIMESTAMP AS _loaded_at
    FROM deduplicated
    WHERE _row_num = 1
)

SELECT *
FROM final
