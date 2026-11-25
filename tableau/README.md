# Tableau | E-Commerce & Supply Chain Analytics
Mac-compatible Tableau Desktop Professional or Public Edition authoring kit. This folder contains instructions and a workflow that packages previously validated historical outputs. It is not a completed Tableau workbook or a Tableau runtime test.

[Historical validation](https://github.com/Krgaurav93084/Amazon-Ecommerce-Growth/actions/runs/45620807997) · [Tableau data-kit workflow](https://github.com/Krgaurav93084/Amazon-Ecommerce-Growth/actions/workflows/tableau-data-kit.yml)

## Build the Tableau dashboard
Connect to the packaged CSV files as separate data sources (do not join aggregate tables at different grains).
| Sheet | Data | Columns | Rows / Marks |
|---|---|---|---|
| Monthly merchandise value | monthly_kpis.csv | Month (continuous date) | SUM(revenue), Line |
| Delivery performance by state | state_kpis.csv | SUM/AVG(on_time_rate) with one row per state | customer_state, Bar |
| Product category value | category_kpis.csv | SUM(revenue) | category, Bar |
| Forecast holdout | forecast_holdout.csv | first date column | Measure Values for actual, model and baseline, Line |
| KPI cards | verified_kpis.csv | metric | value, Text; filter to one metric per card |

### Calculated fields (verified KPI snapshot source)
- Orders: `MAX(IF [metric] = "Orders" THEN [value] END)`
- Delivered merchandise value: `MAX(IF [metric] = "Delivered merchandise value" THEN [value] END)`
- On-time delivery rate: `MAX(IF [metric] = "On-time delivery" THEN [value] END)`
- Cancellation rate: `MAX(IF [metric] = "Cancellation rate" THEN [value] END)`
- Average order value: `MAX(IF [metric] = "Average order value" THEN [value] END)`
Format rates as percentages and values in BRL. Never sum mixed-unit KPI rows. State delivery rates are already aggregated; do not average across states to estimate the overall rate. Expected values: 99,441 orders; BRL 13,221,498.11 merchandise value; 93.23% on time; 0.63% canceled; BRL 137.04 AOV. Forecast models were evaluated against baselines, which performed better.

Suggested layout: 1280 x 800; four KPI cards across top, monthly trend and state bars across middle, category and forecast charts along bottom. Use data-source-specific filters (month, state, category); do not imply cross-filtering unrelated aggregates.

## Open and publish on a Mac
1. Download the Tableau data-kit ZIP from the latest successful workflow and extract it.
2. In Tableau Desktop, Connect > Text File and select the required CSVs. Verify column types and calculations; create the worksheets and dashboard described above.
3. Compare displayed values with the validated findings in the repository. Save a packaged workbook (.twbx) using File > Save As.
4. For a public portfolio, use Server > Tableau Public > Save to Tableau Public with your own authenticated Tableau account. Use only public, non-confidential data and respect the original dataset license. Save an actual image of the rendered dashboard and upload the workbook, screenshot and public link to GitHub.
5. Record Tableau version, tested metrics, and any differences.

The existing Power BI project remains separate. Tableau calculations do not execute DAX or Power Query. This kit has not been opened in Tableau; no workbook, screenshot or public Tableau link is claimed.
