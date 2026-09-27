import sqlite3

conn = sqlite3.connect("nifty100.db")

conn.execute("DELETE FROM balancesheet")

conn.commit()
conn.close()

print("Balancesheet table cleared.")