WITH orders AS (
    SELECT *
    FROM {{ ref('faker_orders') }}
),

returns AS (
    SELECT *
    FROM {{ ref('faker_returns') }}
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
        r.return_id,
        r.return_date,
        r.reason AS return_reason,
        r.refund_amount,
        o._dlt_load_id,
        o._dlt_id,
        'fct_orders' AS _source,
        r.return_id IS NOT NULL AS has_return,
        CURRENT_TIMESTAMP AS _loaded_at
    FROM orders AS o
    LEFT JOIN returns AS r
        ON o.order_id = r.order_id
)

SELECT *
FROM final
