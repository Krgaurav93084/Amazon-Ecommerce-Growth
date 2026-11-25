"""Independent retail and logistics simulation; no Amazon data."""
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from scipy.stats import norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"

def generate():
    rng = np.random.default_rng(42)
    n = 30000
    dates = pd.date_range("2023-01-01", "2025-12-31")
    weights = 1 + .3*np.sin(np.arange(len(dates))*2*np.pi/365) + np.arange(len(dates))/len(dates)
    customers = pd.DataFrame({"customer_id":range(1,5001),"region":rng.choice(["North","South","East","West"],5000)})
    products = pd.DataFrame({"product_id":range(1,101),"category":rng.choice(["Home","Office","Technology","Fashion"],100),"price":rng.uniform(10,200,100).round(2)})
    products["cost"]=(products.price*rng.uniform(.4,.85,100)).round(2)
    orders=pd.DataFrame({"order_id":range(1,n+1),"customer_id":rng.integers(1,5001,n),"product_id":rng.integers(1,101,n),"order_date":pd.to_datetime(rng.choice(dates,n,p=weights/weights.sum())),"quantity":rng.integers(1,5,n),"warehouse":rng.choice(["A","B","C"],n),"status":rng.choice(["delivered","cancelled","returned"],n,p=[.91,.05,.04])})
    orders=orders.merge(products,on="product_id",validate="many_to_one")
    orders["promised_date"]=orders.order_date+pd.Timedelta(days=5)
    delay=rng.poisson(4,n)+1+2*(orders.warehouse=="C").astype(int)
    orders["delivery_date"]=(orders.order_date+pd.to_timedelta(delay,unit="D")).where(orders.status!="cancelled")
    orders["revenue"]=(orders.quantity*orders.price).where(orders.status=="delivered",0).round(2)
    orders["gross_profit"]=(orders.quantity*(orders.price-orders.cost)).where(orders.status=="delivered",0).round(2)
    orders=orders.drop(columns=["category","price","cost"])
    raw=pd.concat([orders,orders.iloc[:20]],ignore_index=True)
    raw.loc[0,"warehouse"]=None
    experiment=pd.DataFrame({"visitor_id":range(1,20001),"variant":rng.choice(["A","B"],20000)})
    experiment["converted"]=(rng.random(len(experiment))<np.where(experiment.variant=="A",.10,.115)).astype(int)
    return raw,customers,products,experiment

def clean(raw,customers,products):
    duplicates=raw.duplicated("order_id")
    unique=raw.loc[~duplicates].copy()
    invalid=(unique[["order_id","customer_id","product_id","order_date","warehouse","quantity","status","promised_date","revenue","gross_profit"]].isna().any(axis=1)|~unique.customer_id.isin(customers.customer_id)|~unique.product_id.isin(products.product_id)|(unique.quantity<=0)|(unique.revenue<0)|~unique.status.isin(["delivered","cancelled","returned"])|((unique.status!="cancelled")&(unique.delivery_date.isna()|(unique.delivery_date<unique.order_date))))
    valid=unique.loc[~invalid].copy()
    valid["on_time"]=np.where(valid.status=="cancelled",np.nan,(valid.delivery_date<=valid.promised_date).astype(int))
    quality=pd.DataFrame({"metric":["raw_rows","duplicate_rows","invalid_unique_rows","accepted_rows"],"value":[len(raw),int(duplicates.sum()),int(invalid.sum()),len(valid)]})
    assert valid.order_id.is_unique
    assert len(raw)==len(valid)+duplicates.sum()+invalid.sum()
    return valid,quality,unique.loc[invalid]

def experiment_analysis(experiment):
    s=experiment.groupby("variant").converted.agg(["sum","count","mean"])
    a,b=s.loc["A"],s.loc["B"]
    p=(a["sum"]+b["sum"])/(a["count"]+b["count"])
    diff=b["mean"]-a["mean"]
    se0=np.sqrt(p*(1-p)*(1/a["count"]+1/b["count"]))
    se=np.sqrt(a["mean"]*(1-a["mean"])/a["count"]+b["mean"]*(1-b["mean"])/b["count"])
    return pd.DataFrame([{"rate_A":a["mean"],"rate_B":b["mean"],"absolute_lift":diff,"relative_lift":diff/a["mean"],"p_value":2*norm.sf(abs(diff/se0)),"ci_low":diff-1.96*se,"ci_high":diff+1.96*se,"n_A":a["count"],"n_B":b["count"]}])

def forecasting(monthly):
    # Chronological 6-month holdout; compare two simple baselines.
    y=monthly.set_index(pd.to_datetime(monthly.month)).revenue.asfreq("MS")
    train,test=y.iloc[:-6],y.iloc[-6:]
    seasonal=pd.Series(y.iloc[-18:-12].values,index=test.index)
    trailing=pd.Series(train.iloc[-3:].mean(),index=test.index)
    scores=pd.DataFrame({"model":["seasonal_naive","trailing_3m"],"mae":[abs(test-seasonal).mean(),abs(test-trailing).mean()]})
    winner=scores.loc[scores.mae.idxmin(),"model"]
    dates=pd.date_range(y.index[-1]+pd.offsets.MonthBegin(),periods=3,freq="MS")
    future=pd.Series(y.iloc[-12:-9].values if winner=="seasonal_naive" else [y.iloc[-3:].mean()]*3,index=dates)
    return scores,pd.DataFrame({"actual":test,"seasonal_naive":seasonal,"trailing_3m":trailing}),future.rename("forecast").to_frame()

def run():
    OUT.mkdir(exist_ok=True)
    raw,c,p,e=generate()
    o,q,reject=clean(raw,c,p)
    calendar=pd.DataFrame({"date":pd.date_range("2023-01-01","2025-12-31")})
    calendar["month"]=calendar.date.dt.strftime("%Y-%m")
    calendar["year"]=calendar.date.dt.year
    tables={"fact_orders":o,"dim_customer":c,"dim_product":p,"dim_date":calendar,"experiment":e,"quality":q}
    with sqlite3.connect(OUT/"retail.sqlite") as conn:
        for name,df in tables.items():
            export=df.copy()
            for col in export.select_dtypes(include=["datetime"]).columns:
                export[col]=export[col].dt.strftime("%Y-%m-%d")
            export.to_sql(name,conn,index=False,if_exists="replace")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_order ON fact_orders(order_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS ix_date ON fact_orders(order_date)")
        conn.executescript((ROOT/"analysis.sql").read_text())
        views={v:pd.read_sql_query("SELECT * FROM "+v,conn) for v in ["monthly_kpis","top_products","warehouse_kpis","customer_rfm","cohort_retention"]}
    ab=experiment_analysis(e)
    scores,holdout,future=forecasting(views["monthly_kpis"].sort_values("month"))
    outputs={**views,**tables,"rejected":reject,"ab_test":ab,"forecast_scores":scores}
    for name,df in outputs.items():
        df.to_csv(OUT/(name+".csv"),index=False)
    holdout.to_csv(OUT/"forecast_holdout.csv")
    future.to_csv(OUT/"forecast_future.csv")
    m=views["monthly_kpis"].sort_values("month"); w=views["warehouse_kpis"]
    fig,ax=plt.subplots(2,2,figsize=(12,8),layout="constrained")
    ax[0,0].plot(pd.to_datetime(m.month),m.revenue);ax[0,0].set_title("Monthly revenue")
    ax[0,1].bar(w.warehouse,100*w.on_time_rate);ax[0,1].set_title("On-time delivery (%)");ax[0,1].set_ylim(0,100)
    ax[1,0].bar(["A","B"],100*ab[["rate_A","rate_B"]].iloc[0]);ax[1,0].set_title("Simulated experiment conversion (%)")
    ax[1,1].plot(holdout.index,holdout.actual,label="Actual");ax[1,1].plot(holdout.index,holdout.seasonal_naive,label="Seasonal");ax[1,1].plot(holdout.index,holdout.trailing_3m,label="Trailing");ax[1,1].legend();ax[1,1].set_title("Forecast validation")
    fig.suptitle("Retail analytics | simulated data");fig.savefig(OUT/"dashboard.png",dpi=150);plt.close(fig)
    with pd.ExcelWriter(OUT/"retail_report.xlsx",engine="openpyxl") as writer:
        for name,df in {**views,"quality":q,"ab_test":ab,"forecast_scores":scores}.items():
            df.to_excel(writer,sheet_name=name[:31],index=False)
            sheet=writer.sheets[name[:31]];sheet.freeze_panes="A2";sheet.auto_filter.ref=sheet.dimensions
    print(q.to_string(index=False));print(scores.to_string(index=False));print(ab.to_string(index=False))

if __name__=="__main__":
    run()
