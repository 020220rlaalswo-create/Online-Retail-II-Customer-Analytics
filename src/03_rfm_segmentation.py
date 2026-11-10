"""03. RFM scoring, rule-based segmentation, charts."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import squarify

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / 'data' / 'processed' / 'online_retail_cleaned.csv', parse_dates=['InvoiceDate'])

df['TotalPrice'] = df['Quantity'] * df['Price']
snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)

rfm = df.groupby('Customer ID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days,   # Recency
    'Invoice': 'nunique',                                        # Frequency
    'TotalPrice': 'sum',                                         # Monetary
}).reset_index()
rfm.columns = ['Customer ID', 'Recency', 'Frequency', 'Monetary']

# Recency: lower is better -> reversed labels. Frequency uses rank() because of many ties (1 purchase).
rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5]).astype(int)


def rfm_segment(row):
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    if r >= 4 and f >= 4 and m >= 4: return 'Champions'
    elif r >= 3 and f >= 3 and m >= 3: return 'Loyal Customers'
    elif r >= 4 and f <= 2: return 'New Customers'
    elif r >= 3 and f <= 2 and m <= 2: return 'Promising'
    elif r <= 2 and f >= 4 and m >= 4: return 'At Risk'
    elif r <= 2 and f >= 3: return 'Cant Lose Them'
    elif r <= 2 and f <= 2 and m >= 3: return 'Hibernating'
    else: return 'Lost'


rfm['Segment'] = rfm.apply(rfm_segment, axis=1)
rfm.to_csv(BASE / 'data' / 'processed' / 'rfm_segments.csv', index=False)

summary = rfm.groupby('Segment').agg(
    Customer_Count=('Customer ID', 'count'),
    Avg_Recency=('Recency', 'mean'),
    Avg_Frequency=('Frequency', 'mean'),
    Avg_Monetary=('Monetary', 'mean'),
    Total_Revenue=('Monetary', 'sum'),
).round(1)
summary['Customer_Share(%)'] = (summary['Customer_Count'] / summary['Customer_Count'].sum() * 100).round(1)
summary['Revenue_Share(%)'] = (summary['Total_Revenue'] / rfm['Monetary'].sum() * 100).round(1)
summary = summary.sort_values('Total_Revenue', ascending=False)
summary.to_csv(BASE / 'data' / 'processed' / 'segment_summary.csv')
print(rfm[['Recency', 'Frequency', 'Monetary']].describe().round(1))
print(summary)

# --- chart 1: customer share vs revenue share
order = summary.index.tolist()
x = np.arange(len(order)); w = 0.35
fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(x - w/2, summary['Customer_Share(%)'], w, label='Customer share (%)', color='#94a3b8')
ax.bar(x + w/2, summary['Revenue_Share(%)'], w, label='Revenue share (%)', color='#2563eb')
ax.set_xticks(x); ax.set_xticklabels(order, rotation=30, ha='right')
ax.set_ylabel('Share (%)'); ax.set_title('Customer share vs revenue share by RFM segment'); ax.legend()
plt.tight_layout(); plt.savefig(BASE / 'images' / 'segment_share_bar.png', dpi=130); plt.close()

# --- chart 2: treemap (box size = customers, label = revenue share)
plt.figure(figsize=(12, 7))
squarify.plot(
    sizes=summary['Customer_Count'],
    label=[f'{s}\n{c:,} customers\n{r}% of revenue' for s, c, r in zip(
        summary.index, summary['Customer_Count'], summary['Revenue_Share(%)'])],
    color=plt.cm.Blues(np.linspace(0.35, 0.85, len(summary))),
    text_kwargs={'fontsize': 10}, pad=True,
)
plt.title('Customer segments (box size = customers, label = revenue share)')
plt.axis('off'); plt.tight_layout()
plt.savefig(BASE / 'images' / 'segment_treemap.png', dpi=130); plt.close()
