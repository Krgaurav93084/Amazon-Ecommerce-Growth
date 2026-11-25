CREATE VIEW olist_portfolio.monthly_kpis AS
WITH m AS (
SELECT date_trunc('month',purchase_date)::date month, count(*) orders,
count(*) FILTER(WHERE order_status='delivered') delivered_orders,
sum(sales_value) revenue,
avg(sales_value) FILTER(WHERE order_status='delivered') aov,
avg((order_status='canceled')::int) cancellation_rate,
avg(on_time) on_time_rate
FROM olist_portfolio.fact_orders GROUP BY 1
), l AS (SELECT *,lag(revenue) OVER(ORDER BY month) previous_revenue FROM m)
SELECT *, (revenue-previous_revenue)/NULLIF(previous_revenue,0) mom_growth FROM l;
CREATE VIEW olist_portfolio.customer_value AS
WITH s AS (SELECT max(purchase_date)::date+1 cutoff FROM olist_portfolio.fact_orders),
r AS (SELECT c.customer_unique_id,count(*) frequency,sum(f.sales_value) historical_merchandise_value,
s.cutoff-max(f.purchase_date)::date recency_days
FROM olist_portfolio.fact_orders f JOIN olist_portfolio.dim_customer c USING(customer_id)
CROSS JOIN s WHERE f.order_status='delivered' GROUP BY c.customer_unique_id,s.cutoff)
SELECT *,CASE WHEN frequency>=2 AND recency_days<=90 THEN 'Repeat recent'
WHEN recency_days>180 THEN 'Inactive in snapshot' ELSE 'Other' END segment FROM r;
CREATE VIEW olist_portfolio.state_kpis AS
SELECT c.customer_state,count(*) orders,sum(f.sales_value) revenue,
count(f.on_time) eligible_deliveries,avg(f.on_time) on_time_rate,avg(f.delivery_days) average_delivery_days
FROM olist_portfolio.fact_orders f JOIN olist_portfolio.dim_customer c USING(customer_id) GROUP BY 1;
CREATE VIEW olist_portfolio.category_kpis AS
SELECT coalesce(p.product_category_name,'Unknown') category,sum(f.price) revenue,
count(*) items,count(DISTINCT f.order_id) distinct_orders
FROM olist_portfolio.fact_items f JOIN olist_portfolio.dim_product p USING(product_id)
WHERE f.order_status='delivered' GROUP BY 1;
