import sqlite3
import pandas as pd

conn = sqlite3.connect("nifty100.db")

df = pd.read_sql("""
PRAGMA table_info(financial_ratios)
""", conn)

print(df[["name", "type"]])

conn.close()