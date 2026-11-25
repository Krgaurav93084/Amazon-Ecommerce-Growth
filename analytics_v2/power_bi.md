# Power BI implementation guide
Run the Python pipeline first. Import output/fact_orders.csv, dim_customer.csv, dim_product.csv and dim_date.csv through Power Query. Set IDs to whole numbers, dates to Date, revenue/cost to decimal, and on_time to nullable whole number. Check errors, nulls and unique dimension keys. Rename the queries to the filenames without extensions.
Create one-to-many single-direction relationships from each dimension key to fact_orders (dim_date[date] -> fact_orders[order_date]). Mark dim_date as a date table. Do not join aggregate views to the fact table.

Create each measure separately:
```dax
Revenue = SUM(fact_orders[revenue])
Gross Profit = SUM(fact_orders[gross_profit])
Gross Margin = DIVIDE([Gross Profit], [Revenue])
Orders = COUNTROWS(fact_orders)
Delivered Orders = CALCULATE([Orders], fact_orders[status] = "delivered")
AOV = DIVIDE([Revenue], [Delivered Orders])
Cancellation Rate = DIVIDE(CALCULATE([Orders],fact_orders[status]="cancelled"),[Orders])
Return Rate = DIVIDE(CALCULATE([Orders],fact_orders[status]="returned"),[Orders])
On Time Rate = AVERAGE(fact_orders[on_time])
Prior Year Revenue = CALCULATE([Revenue], SAMEPERIODLASTYEAR(dim_date[date]))
YoY Growth = DIVIDE([Revenue]-[Prior Year Revenue],[Prior Year Revenue])
Prior Month Revenue = CALCULATE([Revenue], DATEADD(dim_date[date],-1,MONTH))
MoM Growth = DIVIDE([Revenue]-[Prior Month Revenue],[Prior Month Revenue])
```
Pages: executive revenue/margin KPI cards and monthly line; operations warehouse comparison and delivery drill-through; customer region and product category; separate cohort matrix using the cohort CSV (missing cells are not automatically zero). Add slicers for dates, category, region and warehouse. For RLS practice create a role filtering dim_customer[region] = "North"; test as role. Reconcile totals with SQL outputs. Publish to Power BI Service only with appropriate access; scheduled refresh needs configured data source/gateway. This is a build guide, not a completed PBIX or deployed service.
