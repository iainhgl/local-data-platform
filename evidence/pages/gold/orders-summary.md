---
title: Gold Layer - Orders Summary
---

# Orders Summary

Pipeline output from the most recent run. Source: `gold.orders_mart`.

```sql orders_overview
select
  count(*)                                              as total_orders,
  sum(total_amount)                                     as total_revenue,
  sum(case when has_return then 1 else 0 end)           as total_returns,
  round(
    100.0 * sum(case when has_return then 1 else 0 end)
    / count(*), 1
  )                                                     as return_rate_pct
from orders_mart
```

<BigValue data={orders_overview} value="total_orders" title="Total Orders" />
<BigValue data={orders_overview} value="total_revenue" title="Total Revenue ($)" fmt="$#,##0.00" />
<BigValue data={orders_overview} value="return_rate_pct" title="Return Rate (%)" />

```sql orders_by_category
select
  category,
  count(*)          as order_count,
  sum(total_amount) as revenue
from orders_mart
group by category
order by revenue desc
```

<DataTable data={orders_by_category} />
