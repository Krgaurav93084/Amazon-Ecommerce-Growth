# Build Power BI from Olist outputs
Import fact_orders, dim_customer, dim_date, fact_items and dim_product CSVs. Use one-to-many relationships dim_customer[customer_id] -> fact_orders[customer_id], dim_date[purchase_date] -> both fact tables, dim_product[product_id] -> fact_items[product_id]. No direct fact-to-fact relationship. Mark dim_date as date table. Do not use product slicers on order-level metrics unless an explicit bridge is designed. The two fact tables differ in grain.
DAX (each line a separate measure):
```dax
Merchandise Value = SUM(fact_orders[sales_value])
Orders = COUNTROWS(fact_orders)
Delivered Orders = CALCULATE([Orders],fact_orders[order_status]="delivered")
Delivered With Value = CALCULATE([Orders],fact_orders[order_status]="delivered",NOT(ISBLANK(fact_orders[sales_value])))
AOV = DIVIDE([Merchandise Value],[Delivered With Value])
Cancellation Rate = DIVIDE(CALCULATE([Orders],fact_orders[order_status]="canceled"),[Orders])
On Time Rate = AVERAGE(fact_orders[on_time])
Prior Month Sales = CALCULATE([Merchandise Value],DATEADD(dim_date[purchase_date],-1,MONTH))
Monthly Growth = DIVIDE([Merchandise Value]-[Prior Month Sales],[Prior Month Sales])
Category Sales = CALCULATE(SUM(fact_items[price]),fact_items[order_status]="delivered")
```
Import customer_value as a separate full-period snapshot table: Repeat Rate = DIVIDE(CALCULATE(COUNTROWS(customer_value),customer_value[frequency]>1),COUNTROWS(customer_value)). This measure does not respond to order-date slicers. Use forecast_holdout.csv for a dedicated forecast page. Publish only after verifying counts and totals against output/kpis.json. No actual PBIX or Power BI service deployment is included.
