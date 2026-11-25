-- SQLite window functions, CTEs, joins, aggregates and KPI views.
DROP VIEW IF EXISTS monthly_kpis;
CREATE VIEW monthly_kpis AS
WITH m AS (
 SELECT substr(order_date,1,7) month,count(*) orders,
 sum(CASE WHEN status='delivered' THEN 1 ELSE 0 END) delivered_orders,
 sum(revenue) revenue,sum(gross_profit) gross_profit,
 1.0*sum(revenue)/nullif(sum(CASE WHEN status='delivered' THEN 1 ELSE 0 END),0) aov,
 avg(CASE WHEN status='cancelled' THEN 1.0 ELSE 0 END) cancellation_rate,
 avg(CASE WHEN status='returned' THEN 1.0 ELSE 0 END) return_rate
 FROM fact_orders GROUP BY 1
), l AS (
 SELECT *,lag(revenue) OVER(ORDER BY month) prior_month,
 lag(revenue,12) OVER(ORDER BY month) prior_year,
 avg(revenue) OVER(ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) rolling_3m
 FROM m
)
SELECT *,1.0*(revenue-prior_month)/nullif(prior_month,0) mom_growth,
 1.0*(revenue-prior_year)/nullif(prior_year,0) yoy_growth,
 1.0*gross_profit/nullif(revenue,0) gross_margin FROM l;

DROP VIEW IF EXISTS top_products;
CREATE VIEW top_products AS
WITH p AS (
 SELECT substr(o.order_date,1,7) month,d.category,d.product_id,sum(o.revenue) revenue
 FROM fact_orders o JOIN dim_product d USING(product_id) GROUP BY 1,2,3
), r AS (
 SELECT *,dense_rank() OVER(PARTITION BY month,category ORDER BY revenue DESC) revenue_rank FROM p
)
SELECT * FROM r WHERE revenue_rank<=3;

DROP VIEW IF EXISTS warehouse_kpis;
CREATE VIEW warehouse_kpis AS
SELECT warehouse,count(*) orders,avg(on_time) on_time_rate,
 avg(julianday(delivery_date)-julianday(order_date)) avg_delivery_days,
 avg(CASE WHEN status='cancelled' THEN 1.0 ELSE 0 END) cancellation_rate
FROM fact_orders GROUP BY warehouse;

DROP VIEW IF EXISTS customer_rfm;
CREATE VIEW customer_rfm AS
WITH snapshot AS (SELECT date(max(order_date),'+1 day') cutoff FROM fact_orders),
r AS (
 SELECT c.customer_id,c.region,cast(julianday(s.cutoff)-julianday(max(o.order_date)) AS int) recency_days,
 count(o.order_id) frequency,coalesce(sum(o.revenue),0) monetary
 FROM dim_customer c CROSS JOIN snapshot s LEFT JOIN fact_orders o
 ON c.customer_id=o.customer_id AND o.status='delivered'
 GROUP BY c.customer_id,c.region,s.cutoff
)
SELECT *,CASE WHEN frequency=0 THEN 'Never purchased'
 WHEN recency_days<=90 AND frequency>=4 THEN 'Loyal'
 WHEN recency_days>180 THEN 'At risk' ELSE 'Other' END segment FROM r;

DROP VIEW IF EXISTS cohort_retention;
CREATE VIEW cohort_retention AS
WITH activity AS (
 SELECT DISTINCT customer_id,substr(order_date,1,7) month FROM fact_orders WHERE status='delivered'
), first_purchase AS (
 SELECT customer_id,min(month) cohort FROM activity GROUP BY customer_id
), counts AS (
 SELECT f.cohort,a.month,count(*) active_customers,
 (cast(substr(a.month,1,4) AS int)-cast(substr(f.cohort,1,4) AS int))*12+
 cast(substr(a.month,6,2) AS int)-cast(substr(f.cohort,6,2) AS int) month_number
 FROM activity a JOIN first_purchase f USING(customer_id) GROUP BY 1,2
), sizes AS (SELECT cohort,count(*) cohort_size FROM first_purchase GROUP BY cohort)
SELECT counts.*,sizes.cohort_size,1.0*active_customers/cohort_size retention
FROM counts JOIN sizes USING(cohort);
