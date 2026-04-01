WITH customers AS (
    SELECT *
    FROM {{ ref('faker_customers') }}
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
        'dim_customers' AS _source,
        CURRENT_TIMESTAMP AS _loaded_at
    FROM customers
)

SELECT *
FROM final
