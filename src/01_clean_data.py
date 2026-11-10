"""01. Raw data cleaning: merge both sheets, remove noise, save cleaned data."""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / 'data' / 'raw' / 'online_retail_II.xlsx'
OUT = BASE / 'data' / 'processed'
OUT.mkdir(parents=True, exist_ok=True)

df = pd.concat(
    [pd.read_excel(RAW, sheet_name=s) for s in ['Year 2009-2010', 'Year 2010-2011']],
    ignore_index=True,
)
log = [('raw (2 sheets merged)', len(df))]

# 1) exact duplicate rows
df = df.drop_duplicates()
log.append(('drop duplicates', len(df)))

# 2) cancelled orders (Invoice starts with 'C') -> kept separately for return analysis
is_cancel = df['Invoice'].astype(str).str.startswith('C')
df[is_cancel].to_csv(OUT / 'online_retail_cancelled.csv', index=False)
df = df[~is_cancel]
log.append(('remove cancelled orders', len(df)))

# 3) missing Customer ID (guest orders) -> cannot be tracked at customer level
df = df.dropna(subset=['Customer ID'])
log.append(('remove missing Customer ID', len(df)))

# 4) non-positive price / quantity (samples, adjustments)
df = df[(df['Price'] > 0) & (df['Quantity'] > 0)].copy()
df['Customer ID'] = df['Customer ID'].astype(int)
log.append(('remove Price/Quantity <= 0', len(df)))

df.to_csv(OUT / 'online_retail_cleaned.csv', index=False)

prev = None
for step, n in log:
    print(f'{step:<32}{n:>10,}' + (f'  (-{prev - n:,})' if prev else ''))
    prev = n
print('customers:', df['Customer ID'].nunique())
