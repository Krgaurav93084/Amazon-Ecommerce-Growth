# End-to-end retail, logistics and customer analytics
An independent educational case study, not Amazon company data or internship work. Reproducible seeded simulation: 30,000 orders, 5,000 customers, 100 products, 20,000 randomized visitors, 2023–2025. Duplicate and missing records are deliberately injected.

## Run
From this directory: `python -m pip install -r requirements.txt`, then `python run.py`. Outputs: SQLite database, CSV tables, Excel workbook, dashboard PNG, experiment results and forecast validation. Outputs are generated locally and excluded from Git. Python 3.10+ and SQLite 3.25+ recommended.

## Business questions
- How do revenue, gross margin and AOV change month over month and year over year?
- Which products lead each category? Which warehouses miss delivery promises?
- Which customers are at risk? How do first-purchase cohorts retain?
- Does variant B improve conversion? What does its confidence interval imply?
- Which baseline predicts held-out monthly revenue better?

## Methods
Python/Pandas cleaning, reconciliation and assertions; SQLite dimensional model (one row per order, unique dimensions), indexed keys, CTEs, window functions, joins, ranking and cohort analysis; descriptive analysis; two-proportion z-test and 95% CI; chronological forecast holdout comparing seasonal-naive and trailing-average models by MAE; Excel export and matplotlib dashboard. See power_bi.md for Power Query, DAX, modeling, drill-through and RLS exercises.

## KPI definitions and limitations
Revenue and gross profit include delivered orders only; simulated merchandise profit excludes overhead/tax/shipping. AOV uses delivered orders. Cancellation/return rate uses all accepted orders. On-time denominator is non-cancelled orders, including returned orders with delivery timestamps. Cohorts use delivered purchase months, not customer signups; recent cohorts are right-censored and absent activity cells are not automatically zero. Experiment is simulated with independent visitors, not evidence of a real treatment effect. Forecasts are simple educational baselines. No real company performance or savings is claimed. Generated Excel is not evidence of hands-on Excel PivotTable proficiency; the Power BI guide is not a finished dashboard.
