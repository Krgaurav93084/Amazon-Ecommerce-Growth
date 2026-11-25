# Verified Olist analytical findings
Validation date: 25 November 2026. [Successful PostgreSQL pipeline and reconciliation](https://github.com/Krgaurav93084/Amazon-Ecommerce-Growth/actions/runs/45620807997). Independent analysis of the Olist public dataset, not Amazon internal data.
| KPI | Calculated value |
|---|---:|
| Orders | 99,441 |
| Delivered merchandise value | BRL 13,221,498.11 |
| Average order value | BRL 137.04 |
| Observed delivered customers | 93,358 |
| Repeat purchase rate | 3.00% |
| Cancellation rate | 0.63% |
| On-time delivery | 93.23% |
| Lowest on-time state (at least 100 eligible deliveries) | AL, 78.59% |

## Business recommendations
1. Investigate late deliveries in AL; compare route, carrier and regional order mix before concluding causality.
2. Design retention experiments for the low observed repeat purchase rate; the finite observation window is not proof of churn.
3. Use last-month forecast baseline (holdout MAE BRL 90,501.23) rather than damped Holt (BRL 233,388.22).
4. Use the zero baseline for the 90-day customer revenue prediction (MAE BRL 0.83 vs Random Forest BRL 1.82); evaluate alternative approaches before deployment.
5. Track cancellations with clear order-level denominators. No actual net profit, return rate or lifetime profit is available.
[Generated dashboard PNG and aggregate CSVs](https://github.com/Krgaurav93084/Amazon-Ecommerce-Growth/actions/runs/45620807997/artifacts/15024362191) (GitHub artifact retention applies). See the permanent SVG overview alongside this document.
