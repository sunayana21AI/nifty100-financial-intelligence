import sqlite3


database = "nifty100.db"

connection = sqlite3.connect(database)

cursor = connection.cursor()


with open("db/schema.sql", "r") as file:
    schema = file.read()


cursor.executescript(schema)


connection.commit()

connection.close()


print("Database created successfully!")