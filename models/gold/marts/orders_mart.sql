WITH orders AS (
    SELECT *
    FROM {{ ref('fct_orders') }}
),

customers AS (
    SELECT *
    FROM {{ ref('dim_customers') }}
),

products AS (
    SELECT *
    FROM {{ ref('dim_products') }}
),

final AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.product_id,
        o.order_date,
        o.quantity,
        o.unit_price,
        o.total_amount,
        o.status,
        o.created_at,
        o.has_return,
        o.return_id,
        o.return_date,
        o.return_reason,
        o.refund_amount,
        c.first_name,
        c.last_name,
        c.email,
        c.city,
        c.country,
        p.product_name,
        p.category,
        p.sku,
        o._dlt_load_id,
        'orders_mart' AS _source,
        CURRENT_TIMESTAMP AS _loaded_at
    FROM orders AS o
    LEFT JOIN customers AS c
        ON o.customer_id = c.customer_id
    LEFT JOIN products AS p
        ON o.product_id = p.product_id
)

SELECT *
FROM final
