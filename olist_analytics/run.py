"""Independent analytics using Olist public CSVs, not Amazon internal data."""
from pathlib import Path
import argparse, os, json
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent

def load(data):
    def read(name):return pd.read_csv(data/("olist_"+name+"_dataset.csv"))
    o,c,i,p,prod=map(read,["orders","customers","order_items","order_payments","products"])
    quality={x+"_raw":len(d) for x,d in zip(["orders","customers","items","payments","products"],[o,c,i,p,prod])}
    for name,d,keys in [("orders",o,["order_id"]),("customers",c,["customer_id"]),("items",i,["order_id","order_item_id"]),("payments",p,["order_id","payment_sequential"]),("products",prod,["product_id"])]:
        if d[keys].isna().any().any() or d.duplicated(keys).any():raise ValueError(name+": invalid or duplicate primary keys")
    for col in ["order_purchase_timestamp","order_delivered_customer_date","order_estimated_delivery_date"]:
        o[col]=pd.to_datetime(o[col],errors="coerce")
    if o.order_purchase_timestamp.isna().any():raise ValueError("Missing purchase timestamp")
    if not o.customer_id.isin(c.customer_id).all() or not i.order_id.isin(o.order_id).all() or not p.order_id.isin(o.order_id).all() or not i.product_id.isin(prod.product_id).all():raise ValueError("Unmatched foreign key")
    if c.customer_unique_id.isna().any():raise ValueError("Missing customer identity")
    if i[["price","freight_value"]].isna().any().any() or p.payment_value.isna().any() or (i[["price","freight_value"]]<0).any().any() or (p.payment_value<0).any():raise ValueError("Invalid monetary value")
    # Aggregate payments and items separately before joining, avoiding fanout.
    ip=i.groupby("order_id",as_index=False).agg(merchandise_value=("price","sum"),freight_value=("freight_value","sum"),item_count=("order_item_id","count"))
    pp=p.groupby("order_id",as_index=False).agg(payment_value=("payment_value","sum"))
    f=o.merge(c[["customer_id","customer_unique_id","customer_state"]],on="customer_id",validate="many_to_one").merge(ip,on="order_id",how="left",validate="one_to_one").merge(pp,on="order_id",how="left",validate="one_to_one")
    quality["missing_item_total"]=int(f.merchandise_value.isna().sum())
    quality["missing_payment_total"]=int(f.payment_value.isna().sum())
    f["purchase_date"]=f.order_purchase_timestamp.dt.normalize()
    delivered=f.order_status.eq("delivered")
    f["sales_value"]=f.merchandise_value.where(delivered,0)
    f["delivered_payment"]=f.payment_value.where(delivered,0)
    eligible=delivered & f.order_delivered_customer_date.notna() & f.order_estimated_delivery_date.notna() & (f.order_delivered_customer_date>=f.order_purchase_timestamp)
    f["on_time"]=np.where(eligible,(f.order_delivered_customer_date.dt.normalize()<=f.order_estimated_delivery_date.dt.normalize()).astype(int),np.nan)
    f["delivery_days"]=(f.order_delivered_customer_date-f.order_purchase_timestamp).dt.total_seconds().div(86400).where(eligible)
    quality["delivered_missing_items"]=int((delivered&f.merchandise_value.isna()).sum())
    quality["delivered_missing_payments"]=int((delivered&f.payment_value.isna()).sum())
    quality["delivered_without_valid_delivery_timing"]=int((delivered&~eligible).sum())
    assert len(f)==len(o) and f.order_id.is_unique
    dim_customer=c[["customer_id","customer_unique_id","customer_state"]].copy()
    fact=f[["order_id","customer_id","purchase_date","order_status","sales_value","delivered_payment","freight_value","item_count","on_time","delivery_days"]].copy()
    item=i.merge(o[["order_id","order_status","order_purchase_timestamp"]],on="order_id",validate="many_to_one")
    item["purchase_date"]=item.order_purchase_timestamp.dt.normalize()
    fact_item=item[["order_id","order_item_id","product_id","purchase_date","order_status","price","freight_value"]]
    date=pd.DataFrame({"purchase_date":pd.date_range(f.purchase_date.min(),f.purchase_date.max())})
    date["year"]=date.purchase_date.dt.year;date["month"]=date.purchase_date.dt.month
    return f,{"fact_orders":fact,"dim_customer":dim_customer,"dim_product":prod,"fact_items":fact_item,"dim_date":date},quality

def warehouse(tables,url):
    engine=create_engine(url)
    # Dedicated local portfolio database only. Rebuild tables transactionally.
    with engine.begin() as con:
        con.execute(text("CREATE SCHEMA IF NOT EXISTS olist_portfolio"))
        con.execute(text("DROP VIEW IF EXISTS olist_portfolio.monthly_kpis"))
        con.execute(text("DROP VIEW IF EXISTS olist_portfolio.customer_value"))
        con.execute(text("DROP VIEW IF EXISTS olist_portfolio.state_kpis"))
        con.execute(text("DROP VIEW IF EXISTS olist_portfolio.category_kpis"))
        for name,df in tables.items():df.to_sql(name,con,schema="olist_portfolio",index=False,if_exists="replace")
        for name,key in [("fact_orders","order_id"),("dim_customer","customer_id"),("dim_product","product_id"),("dim_date","purchase_date"),("fact_items","order_id,order_item_id")]:
            con.execute(text(f"ALTER TABLE olist_portfolio.{name} ADD PRIMARY KEY ({key})"))
        con.execute(text("CREATE INDEX ON olist_portfolio.fact_orders(purchase_date)"))
        for statement in (ROOT/"analysis.sql").read_text().split(";"):
            if statement.strip():con.execute(text(statement))
        result={v:pd.read_sql_query(text("SELECT * FROM olist_portfolio."+v),con) for v in ["monthly_kpis","customer_value","state_kpis","category_kpis"]}
    engine.dispose();return result

def forecast(f):
    # Exclude potentially incomplete edge months; explicit stable historical analysis window.
    y=f.loc[(f.purchase_date>="2017-01-01")&(f.purchase_date<"2018-09-01")].groupby(pd.Grouper(key="purchase_date",freq="MS")).sales_value.sum().asfreq("MS",fill_value=0)
    train,test=y.iloc[:-4],y.iloc[-4:]
    model=ExponentialSmoothing(train,trend="add",damped_trend=True,initialization_method="estimated").fit()
    predicted=model.forecast(len(test)).clip(lower=0)
    naive=pd.Series(train.iloc[-1],index=test.index)
    scores=pd.DataFrame({"model":["damped_Holt","last_month"],"mae":[mean_absolute_error(test,predicted),mean_absolute_error(test,naive)]})
    winner=scores.loc[scores.mae.idxmin(),"model"]
    idx=pd.date_range(y.index[-1]+pd.offsets.MonthBegin(),periods=3,freq="MS")
    future=(ExponentialSmoothing(y,trend="add",damped_trend=True,initialization_method="estimated").fit().forecast(3).clip(lower=0) if winner=="damped_Holt" else pd.Series(y.iloc[-1],index=idx))
    return scores,pd.DataFrame({"actual":test,"model":predicted,"baseline":naive}),future.rename("forecast").to_frame()

def customer_prediction(f):
    # Predict 90-day merchandise revenue for existing customers; not lifetime profit.
    def snapshot(cutoff):
        cutoff=pd.Timestamp(cutoff)
        past=f[(f.purchase_date<cutoff)&f.order_status.eq("delivered")&f.sales_value.notna()]
        base=past.groupby("customer_unique_id").agg(last=("purchase_date","max"),frequency=("order_id","count"),monetary=("sales_value","sum"))
        base["recency"]=(cutoff-base.pop("last")).dt.days
        future=f[(f.purchase_date>=cutoff)&(f.purchase_date<cutoff+pd.Timedelta(days=90))&f.order_status.eq("delivered")].groupby("customer_unique_id").sales_value.sum()
        base["target"]=future.reindex(base.index).fillna(0)
        return base
    train=snapshot("2017-12-01");test=snapshot("2018-05-01")
    cols=["frequency","monetary","recency"]
    model=RandomForestRegressor(n_estimators=60,max_depth=5,min_samples_leaf=40,random_state=42,n_jobs=-1)
    model.fit(train[cols],train.target)
    test["prediction_90d"]=model.predict(test[cols])
    scores={"model_mae":float(mean_absolute_error(test.target,test.prediction_90d)),"zero_baseline_mae":float(test.target.abs().mean()),"train_customers":len(train),"test_customers":len(test)}
    return test.reset_index(),scores

def run(data,out,url):
    out.mkdir(parents=True,exist_ok=True)
    f,tables,quality=load(data)
    views=warehouse(tables,url)
    scores,holdout,future=forecast(f)
    predictions,model_scores=customer_prediction(f)
    for n,d in {**views,**tables,"forecast_scores":scores,"customer_prediction":predictions}.items():d.to_csv(out/(n+".csv"),index=False)
    holdout.to_csv(out/"forecast_holdout.csv");future.to_csv(out/"forecast_future.csv")
    (out/"quality.json").write_text(json.dumps(quality,indent=2))
    (out/"customer_model.json").write_text(json.dumps(model_scores,indent=2))
    delivered=f[f.order_status.eq("delivered")]
    customers=views["customer_value"]
    repeat=(customers.frequency>1).mean()
    k={"orders":len(f),"delivered_merchandise_value_brl":float(delivered.sales_value.sum()),"aov_brl":float(delivered.sales_value.mean()),"repeat_purchase_rate":float(repeat),"cancellation_rate":float(f.order_status.eq("canceled").mean()),"on_time_rate":float(f.on_time.mean()),"observed_customers":len(customers)}
    (out/"kpis.json").write_text(json.dumps(k,indent=2))
    states=views["state_kpis"].dropna(subset=["on_time_rate"]);states=states[states.eligible_deliveries>=100]
    worst=states.loc[states.on_time_rate.idxmin()] if len(states) else None
    report=["# Calculated findings — Olist historical dataset",f"Delivered merchandise value: BRL {k['delivered_merchandise_value_brl']:,.2f}; AOV BRL {k['aov_brl']:,.2f}.",f"Repeat purchase rate: {repeat:.2%}; prioritize retention experiments rather than infer churn.",f"Cancellation rate: {k['cancellation_rate']:.2%}; investigate by state and category with appropriate denominators.",f"On-time delivery: {k['on_time_rate']:.2%}.",f"Lowest on-time state with >=100 valid deliveries: {worst.customer_state} ({worst.on_time_rate:.2%}); investigate carrier and delivery routes." if worst is not None else "Insufficient state-level delivery coverage.",f"Forecast holdout MAE: {scores.to_dict(orient='records')}. Compare forecast to baseline before planning.",f"90-day customer revenue model MAE: {model_scores['model_mae']:.2f} BRL vs zero baseline {model_scores['zero_baseline_mae']:.2f} BRL. Not lifetime value."]
    (out/"findings.md").write_text("\n\n".join(report))
    m=views["monthly_kpis"].sort_values("month")
    fig,ax=plt.subplots(2,2,figsize=(13,8),layout="constrained")
    ax[0,0].plot(pd.to_datetime(m.month),m.revenue);ax[0,0].set_title("Delivered merchandise value (BRL)")
    if len(states):states.nsmallest(10,"on_time_rate").set_index("customer_state").on_time_rate.mul(100).plot.barh(ax=ax[0,1],title="Lowest on-time rates (%)")
    views["category_kpis"].nlargest(10,"revenue").set_index("category").revenue.plot.barh(ax=ax[1,0],title="Top categories by delivered merchandise value")
    holdout.plot(ax=ax[1,1],title="Forecast vs actual (BRL)")
    fig.suptitle("Olist historical retail analytics");fig.savefig(out/"dashboard.png",dpi=150);plt.close(fig)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("data",type=Path);p.add_argument("--output",type=Path,default=ROOT/"output");a=p.parse_args()
    url=os.environ.get("OLIST_DATABASE_URL")
    if not url or not url.startswith("postgresql"):p.error("Set OLIST_DATABASE_URL to a dedicated PostgreSQL database")
    run(a.data,a.output,url)
