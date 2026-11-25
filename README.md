# Amazon E-Commerce — Growth, BI Maturity & Data Warehouse Analysis

## Overview
This project analyzes Amazon.com, Inc.'s Business Intelligence maturity,
data sources, and data-warehousing infrastructure, and proposes
dashboards for sales, profitability, and advertising performance.

## Key Topics Covered
1. **About Amazon** — founded 1994 by Jeff Bezos; e-commerce, cloud
   (AWS), streaming, and AI business lines.
2. **BI Maturity Level** — assessed at Gartner's **"Level 5: Optimization"**,
   with a target of expanding predictive/prescriptive analytics and
   maximizing use of Machine Learning across the business.
3. **Data Sources** — customer data, sales/transaction data, website/app
   tracking, Alexa/smart devices, third-party seller data, advertising
   data, social media, and IoT devices.
4. **Data Warehouse Infrastructure** — Amazon uses an **ELT** (Extract,
   Load, Transform) approach via **Amazon Redshift**, with **AWS Glue**
   handling ETL-style ingestion from streaming sources (e.g., Kafka).
   ELT is preferred over ETL for flexibility, scalability, cost
   efficiency, and simpler pipelines.
5. **Proposed Dashboards** — Sales Metrics Analysis (monthly sales,
   profit by category, quantity by state), and Amazon Advertising
   dashboards (spend, revenue, ACOS, ROAS by product category and week).

## Files
- `etl_pipeline.py` — A runnable, simplified stand-in for Amazon's ELT
  architecture (Extract → Load → Transform), using `pandas` + `sqlite3`
  in place of AWS Glue + Amazon Redshift:
  - **Extract**: simulates pulling raw sales and advertising data.
  - **Load**: loads raw data into warehouse tables (`sales_raw`, `ads_raw`).
  - **Transform**: runs SQL inside the "warehouse" to calculate profit
    contribution by product category and weekly advertising **ACOS**
    (Ad Cost of Sales) / **ROAS** (Return on Ad Spend) — the same metrics
    shown in the project's dashboards.
  - Run with: `python3 etl_pipeline.py`
  - To adapt to real AWS infrastructure, swap the extract functions for
    `boto3`/S3 reads and the `sqlite3` connection for a Redshift
    connection (e.g., `redshift_connector`).

## Recommendations (from the project)
- Strengthen relationships and localize offerings in high-performing
  states (e.g., California).
- Reduce ad spend on low-revenue categories (pens, color cartridges,
  printers).
- Improve product discoverability / search ranking.
- Expand into new customer-centric markets, leveraging Amazon's success
  in cloud, entertainment, and smart devices.

## Challenges
- Understanding and explaining Amazon's hybrid ETL + ELT approach.
- Designing a scalable warehouse for massive data volume.
- Accounting for advertising metrics that change frequently.
- Explaining Amazon's complex, multi-domain infrastructure
  (e-commerce, cloud, logistics).

## References
- Amazon (2022). *Facts.* About Amazon. https://www.aboutamazon.com/facts
- Amazon Web Services, Inc. (n.d.). *ETL vs. ELT - Comparing
  Data-Processing Approaches.* https://aws.amazon.com/compare/the-difference-between-etl-and-elt/
- Forbes (2021). *Predicting The Future Of Demand: How Amazon Is
  Reinventing Forecasting With Machine Learning.*
- Gartner (2015). *ITScore Overview for BI and Analytics.*
- GeneAka (2022). *Build a modern data architecture on AWS...*

## Portfolio analytics upgrades
- [Public Olist PostgreSQL analytics](olist_analytics/README.md): real-data ingestion code, KPI analysis, forecast and customer revenue prediction. Dataset download and execution required.
- [Synthetic retail simulation](analytics_v2/README.md): reproducible simulated orders, A/B testing and Excel reporting. Neither extension uses Amazon internal data.
