import sqlite3

conn = sqlite3.connect("nifty100.db")
cursor = conn.cursor()

columns = [
    ("equity_capital", "REAL"),
    ("reserves", "REAL"),
    ("borrowings", "REAL"),
    ("other_liabilities", "REAL")
]

for column_name, data_type in columns:
    try:
        cursor.execute(
            f"ALTER TABLE balancesheet ADD COLUMN {column_name} {data_type}"
        )
        print(f"✓ Added column: {column_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"✓ Column already exists: {column_name}")
        else:
            raise

conn.commit()
conn.close()

print("\nBalancesheet table updated successfully.")