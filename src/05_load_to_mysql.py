"""05. Load the cleaned data into MySQL so the sql/*.sql files can be run.

Usage (credentials via environment variables, never hard-code a password):
    set MYSQL_USER=root
    set MYSQL_PASSWORD=your_password
    set MYSQL_DB=retail2        # the database must already exist: CREATE DATABASE retail2;
    python src/05_load_to_mysql.py
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine

BASE = Path(__file__).resolve().parents[1]
user = os.environ.get('MYSQL_USER', 'root')
password = quote_plus(os.environ['MYSQL_PASSWORD'])   # quote_plus handles special characters
host = os.environ.get('MYSQL_HOST', 'localhost')
db = os.environ.get('MYSQL_DB', 'retail2')

engine = create_engine(f'mysql+pymysql://{user}:{password}@{host}:3306/{db}')
df = pd.read_csv(BASE / 'data' / 'processed' / 'online_retail_cleaned.csv', parse_dates=['InvoiceDate'])
df.to_sql('online_retail_clean', con=engine, if_exists='replace', index=False, chunksize=50000)
print('loaded', len(df), 'rows into', db + '.online_retail_clean')
