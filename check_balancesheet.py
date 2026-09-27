import sqlite3
import pandas as pd

conn = sqlite3.connect("nifty100.db")

print(pd.read_sql("""
SELECT *
FROM balancesheet
WHERE company_id = 1
""", conn))

conn.close()