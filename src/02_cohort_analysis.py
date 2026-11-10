"""02. Cohort retention analysis + heatmap."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

BASE = Path(__file__).resolve().parents[1]
df = pd.read_csv(BASE / 'data' / 'processed' / 'online_retail_cleaned.csv', parse_dates=['InvoiceDate'])

df['InvoiceMonth'] = df['InvoiceDate'].dt.to_period('M')
df['CohortMonth'] = df.groupby('Customer ID')['InvoiceMonth'].transform('min')
df['CohortIndex'] = (
    (df['InvoiceMonth'].dt.year - df['CohortMonth'].dt.year) * 12
    + (df['InvoiceMonth'].dt.month - df['CohortMonth'].dt.month)
)

cohort_data = df.groupby(['CohortMonth', 'CohortIndex'])['Customer ID'].nunique().reset_index()
cohort_pivot = cohort_data.pivot(index='CohortMonth', columns='CohortIndex', values='Customer ID')
retention = cohort_pivot.divide(cohort_pivot.iloc[:, 0], axis=0) * 100
retention.round(1).to_csv(BASE / 'data' / 'processed' / 'cohort_retention.csv')

plt.figure(figsize=(15, 8))
sns.heatmap(retention, annot=True, fmt='.0f', cmap='Blues', vmin=0, vmax=50)
plt.title('Cohort Retention Rate (%)')
plt.xlabel('Months since first purchase (CohortIndex)')
plt.ylabel('Cohort month (first purchase)')
plt.tight_layout()
plt.savefig(BASE / 'images' / 'cohort_retention_heatmap.png', dpi=130)

# quick numbers used in the README
print('2009-12 cohort size:', int(cohort_pivot.iloc[0, 0]))
post = retention.loc['2010-01':'2011-11', 1]
print('month-1 retention, cohorts 2010-01..2011-11: mean %.1f, min %.1f (%s), max %.1f (%s)' % (
    post.mean(), post.min(), post.idxmin(), post.max(), post.idxmax()))
print('2010-12 cohort size:', int(cohort_pivot.loc['2010-12', 0]))

# --- calendar-month view: average retention of 2010+ cohorts by the calendar month in which they re-purchased
rows = []
for cohort in retention.index:
    if str(cohort) < '2010-01':
        continue                       # 2009-12 cohort excluded (left-censoring)
    for idx in retention.columns:
        v = retention.loc[cohort, idx]
        if idx >= 1 and pd.notna(v):
            rows.append(((cohort + int(idx)).strftime('%Y-%m'), v))
cal = pd.DataFrame(rows, columns=['calendar_month', 'retention']).groupby('calendar_month')['retention'].agg(['mean', 'count']).round(1)
cal.to_csv(BASE / 'data' / 'processed' / 'calendar_month_retention.csv')

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(cal.index, cal['mean'], marker='o', color='#2563eb')
ax.set_title('Average retention of 2010+ cohorts by calendar month (Dec 2011 = partial month)')
ax.set_ylabel('Mean retention (%)')
plt.xticks(rotation=60, ha='right'); ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(BASE / 'images' / 'calendar_month_retention.png', dpi=130); plt.close()
print(cal.loc['2010-09':'2010-12'].T.to_string())
