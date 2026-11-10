"""04. Heuristic 12-month annualized revenue projection, NOT validated future LTV.

The first-to-last purchase observation window can inflate short-tenure customers.
Compare against temporal holdout results from 06_ltv_backtest.py before using
these values for decisions. The 180-day decay is an illustrative assumption.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / 'data' / 'processed' / 'online_retail_cleaned.csv', parse_dates=['InvoiceDate'])
rfm = pd.read_csv(BASE / 'data' / 'processed' / 'rfm_segments.csv')

period = df.groupby('Customer ID')['InvoiceDate'].agg(['min', 'max'])
period['ObservationMonths'] = ((period['max'] - period['min']).dt.days / 30).clip(lower=1)
rfm = rfm.merge(period[['ObservationMonths']], on='Customer ID')

rfm['AOV'] = rfm['Monetary'] / rfm['Frequency']
rfm['PurchaseFreqPerMonth'] = rfm['Frequency'] / rfm['ObservationMonths']
rfm['Predicted_LTV_12M'] = rfm['AOV'] * rfm['PurchaseFreqPerMonth'] * 12   # = Monetary / months * 12

# adjustment 1: binary (active if last purchase within 180 days)
rfm['Adjusted_LTV_binary'] = rfm['Predicted_LTV_12M'] * (rfm['Recency'] <= 180).astype(int)
# adjustment 2: continuous exponential decay on recency
rfm['Adjusted_LTV_decay'] = rfm['Predicted_LTV_12M'] * np.exp(-rfm['Recency'] / 180)
rfm.to_csv(BASE / 'data' / 'processed' / 'rfm_ltv.csv', index=False)

ltv = rfm.groupby('Segment').agg(
    Customers=('Customer ID', 'count'),
    Original_mean=('Predicted_LTV_12M', 'mean'),
    Binary_mean=('Adjusted_LTV_binary', 'mean'),
    Decay_mean=('Adjusted_LTV_decay', 'mean'),
    Original_sum=('Predicted_LTV_12M', 'sum'),
    Decay_sum=('Adjusted_LTV_decay', 'sum'),
).round(1)
ltv['Decay_change(%)'] = ((ltv['Decay_mean'] / ltv['Original_mean'] - 1) * 100).round(0)
ltv = ltv.sort_values('Decay_sum', ascending=False)
ltv['Decay_sum_share(%)'] = (ltv['Decay_sum'] / ltv['Decay_sum'].sum() * 100).round(1)
ltv.to_csv(BASE / 'data' / 'processed' / 'ltv_by_segment.csv')
print(ltv)
print('\nTop 5 by original LTV:')
print(rfm.nlargest(5, 'Predicted_LTV_12M')[['Customer ID', 'Segment', 'Frequency', 'Monetary', 'ObservationMonths', 'Predicted_LTV_12M']].round(1))

# --- chart: original vs decay-adjusted mean LTV
x = np.arange(len(ltv)); w = 0.35
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(x - w/2, ltv['Original_mean'], w, label='Original projected LTV', color='#94a3b8')
ax.bar(x + w/2, ltv['Decay_mean'], w, label='Recency-decay adjusted LTV', color='#2563eb')
ax.set_xticks(x); ax.set_xticklabels(ltv.index, rotation=30, ha='right')
ax.set_ylabel('Mean 12-month LTV'); ax.set_title('Mean LTV by segment: original vs recency-adjusted'); ax.legend()
plt.tight_layout(); plt.savefig(BASE / 'images' / 'ltv_original_vs_adjusted.png', dpi=130); plt.close()

# --- chart: distribution inside each segment (clipped at the 95th percentile for readability)
rfm.boxplot(column='Adjusted_LTV_decay', by='Segment', rot=30, figsize=(12, 6))
plt.ylim(0, rfm['Adjusted_LTV_decay'].quantile(0.95))
plt.suptitle(''); plt.title('Adjusted LTV distribution by segment (y-axis clipped at 95th percentile)')
plt.ylabel('Adjusted LTV'); plt.xlabel('')
plt.tight_layout(); plt.savefig(BASE / 'images' / 'ltv_boxplot.png', dpi=130); plt.close()
