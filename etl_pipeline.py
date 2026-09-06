"""
Amazon E-Commerce — ELT Pipeline (Extract, Load, Transform)
============================================================
Illustrates the ELT data-warehousing pattern described in the project
(Amazon Redshift + AWS Glue), applied to sales / advertising data used
for the Sales Metrics and Advertising dashboards.

Pattern:
    Extract  -> pull raw data from source systems (S3 / operational DBs)
    Load     -> load raw data as-is into the warehouse (Redshift-style)
    Transform-> run SQL-based transformations inside the warehouse

This script is a lightweight, runnable stand-in for that architecture,
using pandas + sqlite3 so it can run without cloud credentials. Swap the
`load_to_warehouse` / `transform_in_warehouse` functions for real
Amazon Redshift / AWS Glue calls (boto3, redshift-connector, etc.) in
production.
"""

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "warehouse.db"


# ---------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------
def extract_sales_data() -> pd.DataFrame:
    """
    Simulates pulling raw sales/order data from source systems
    (e.g. via AWS Database Migration Service / Amazon S3 landing zone).
    Replace with real extraction logic (API calls, S3 reads, DB queries).
    """
    data = {
        "order_date": pd.date_range("2015-01-01", periods=6, freq="MS"),
        "product_category": ["Furniture", "Office Supplies", "Technology",
                              "Furniture", "Office Supplies", "Technology"],
        "sales": [274767, 326101, 271697, 389832, 306572, 355369],
        "profit": [-8542, 10842, 9182, 41423, 12320, 34765],
        "region": ["West", "Central", "East", "South", "West", "Central"],
    }
    return pd.DataFrame(data)


def extract_advertising_data() -> pd.DataFrame:
    """Simulates pulling weekly Amazon Advertising performance data."""
    data = {
        "week_start": pd.date_range("2019-07-14", periods=5, freq="W"),
        "ad_spend": [55615, 45077, 33340, 26467, 12417],
        "ad_revenue": [205095, 146082, 112019, 100226, 69694],
        "units": [2720, 2078, 1407, 1407, 702],
    }
    df = pd.DataFrame(data)
    df["acos"] = (df["ad_spend"] / df["ad_revenue"]) * 100         # Ad Cost of Sales
    df["roas"] = (df["ad_revenue"] / df["ad_spend"]) * 100         # Return on Ad Spend
    return df


# ---------------------------------------------------------------------
# LOAD  (raw data lands in the warehouse largely unmodified)
# ---------------------------------------------------------------------
def load_to_warehouse(df: pd.DataFrame, table_name: str, conn: sqlite3.Connection) -> None:
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into raw.{table_name}")


# ---------------------------------------------------------------------
# TRANSFORM  (run inside the warehouse using SQL, as Redshift/dbt would)
# ---------------------------------------------------------------------
def transform_in_warehouse(conn: sqlite3.Connection) -> None:
    # Profit contribution by product category
    query_profit_by_category = """
        SELECT product_category,
               SUM(profit) AS total_profit,
               ROUND(100.0 * SUM(profit) / (SELECT SUM(profit) FROM sales_raw), 2) AS pct_of_total_profit
        FROM sales_raw
        GROUP BY product_category
        ORDER BY total_profit DESC;
    """
    result = pd.read_sql(query_profit_by_category, conn)
    print("\n-- Profit contribution by product category --")
    print(result.to_string(index=False))

    # Weekly advertising ROAS / ACOS trend
    query_ad_performance = """
        SELECT week_start, ad_spend, ad_revenue,
               ROUND(acos, 1) AS acos_pct,
               ROUND(roas, 1) AS roas_pct
        FROM ads_raw
        ORDER BY week_start;
    """
    result2 = pd.read_sql(query_ad_performance, conn)
    print("\n-- Weekly Advertising Performance (ACOS / ROAS) --")
    print(result2.to_string(index=False))


# ---------------------------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------------------------
def run_pipeline() -> None:
    conn = sqlite3.connect(DB_PATH)

    # Extract
    sales_df = extract_sales_data()
    ads_df = extract_advertising_data()

    # Load (raw layer)
    load_to_warehouse(sales_df, "sales_raw", conn)
    load_to_warehouse(ads_df, "ads_raw", conn)

    # Transform (analytics layer)
    transform_in_warehouse(conn)

    conn.close()


if __name__ == "__main__":
    run_pipeline()
