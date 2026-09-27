import sqlite3

conn = sqlite3.connect("nifty100.db")
cursor = conn.cursor()

columns = [
    ("return_on_equity_pct", "REAL"),
    ("debt_to_equity", "REAL")
]

for column_name, data_type in columns:
    try:
        cursor.execute(
            f"ALTER TABLE financial_ratios ADD COLUMN {column_name} {data_type}"
        )
        print(f"✓ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"✓ Column already exists: {column_name}")
        else:
            raise

conn.commit()
conn.close()

print("\nfinancial_ratios table updated successfully.")