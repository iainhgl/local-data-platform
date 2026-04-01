WITH products AS (
    SELECT *
    FROM {{ ref('faker_products') }}
),

final AS (
    SELECT
        product_id,
        product_name,
        category,
        unit_price,
        sku,
        created_at,
        _dlt_load_id,
        _dlt_id,
        'dim_products' AS _source,
        CURRENT_TIMESTAMP AS _loaded_at
    FROM products
)

SELECT *
FROM final
