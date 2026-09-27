import sqlite3
import pandas as pd

conn = sqlite3.connect("nifty100.db")

print(pd.read_sql("""
SELECT
COUNT(return_on_equity_pct) AS roe_filled,
COUNT(debt_to_equity) AS de_filled
FROM financial_ratios
""", conn))

print()

print(pd.read_sql("""
SELECT
company_id,
year,
return_on_equity_pct,
debt_to_equity
FROM financial_ratios
LIMIT 10
""", conn))

conn.close()