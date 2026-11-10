"""Temporal holdout validation for simple 12-month revenue projections.

Train: transactions before 2010-12-01
Test:  2010-12-01 through 2011-11-30 (12 complete calendar months).
Evaluate only customers observed before the cutoff; future new customers are excluded.
This is an illustrative baseline comparison, not a trained probabilistic CLV model.
"""
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
CUTOFF = pd.Timestamp('2010-12-01')
END = pd.Timestamp('2011-12-01')  # exclusive; Dec 2011 is incomplete

df = pd.read_csv(
    BASE / 'data' / 'processed' / 'online_retail_cleaned.csv',
    parse_dates=['InvoiceDate'],
)
df['Revenue'] = df['Quantity'] * df['Price']
past = df[df['InvoiceDate'] < CUTOFF].copy()
future = df[(df['InvoiceDate'] >= CUTOFF) & (df['InvoiceDate'] < END)].copy()

if past.empty or future.empty:
    raise ValueError('Insufficient data for historical/future split')

customers = past.groupby('Customer ID').agg(
    first_purchase=('InvoiceDate', 'min'),
    last_purchase=('InvoiceDate', 'max'),
    past_revenue=('Revenue', 'sum'),
)

# Use elapsed time from first purchase to cutoff (not first-to-last transaction).
# This includes inactivity periods and avoids mechanically treating every
# one-time customer as having exactly one month of follow-up.
customers['months_exposed'] = (
    (CUTOFF - customers['first_purchase']).dt.total_seconds() / (86400 * 30.4375)
).clip(lower=1)
customers['recency_days'] = (
    (CUTOFF - customers['last_purchase']).dt.total_seconds() / 86400
).clip(lower=0)
customers['annualized_baseline'] = customers['past_revenue'] / customers['months_exposed'] * 12
customers['recency_adjusted'] = (
    customers['annualized_baseline'] * np.exp(-customers['recency_days'] / 180)
)
actual = future.groupby('Customer ID')['Revenue'].sum()
customers['actual_12m'] = actual.reindex(customers.index, fill_value=0)

def metrics(pred):
    error = pred - customers['actual_12m']
    actual_total = customers['actual_12m'].sum()
    return {
        'MAE': error.abs().mean(),
        'WAPE_pct': error.abs().sum() / actual_total * 100 if actual_total else np.nan,
        'prediction_to_actual_ratio': pred.sum() / actual_total if actual_total else np.nan,
    }

results = pd.DataFrame({
    'annualized_baseline': metrics(customers['annualized_baseline']),
    'recency_adjusted': metrics(customers['recency_adjusted']),
}).T.round(2)
print('Existing customers:', len(customers))
print('Holdout:', CUTOFF.date(), 'to', (END - pd.Timedelta(days=1)).date())
print(results.to_string())
print('Note: values are gross positive transaction revenue; cancellations excluded.')

out = BASE / 'data' / 'processed'
out.mkdir(parents=True, exist_ok=True)
results.to_csv(out / 'ltv_backtest_metrics.csv', index_label='method')
