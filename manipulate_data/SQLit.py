import sqlite3
import csv
import pandas as pd

# Connect to SQLite database (it will be created if it doesn't exist)
conn = sqlite3.connect("glossapi_database.db")
cursor = conn.cursor()

# Create table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS glossapi_data (
    text TEXT,
    ΠΗΓΗ TEXT,
    ΠΕΡΙΟΔΟΣ TEXT,
    ΠΟΙΚΙΛΙΑ TEXT,
    ΔΙΑΛΕΚΤΟΣ TEXT,
    ΠΡΟΣΔΙΟΡΙΣΤΕ TEXT
)
"""
)

# Load CSV data into the SQLite database
with open(
    "/home/fivos/Projects/GlossAPI/manipulate_data/combined_2nd_dataset.csv",
    "r",
    encoding="utf-8",
) as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=",")
    next(csv_reader)  # Skip header row
    for row in csv_reader:
        # Replace empty strings with None (NULL in SQLite)
        row = [None if field == "" else field for field in row]
        cursor.execute(
            """
        INSERT INTO glossapi_data (text, ΠΗΓΗ, ΠΕΡΙΟΔΟΣ, ΠΟΙΚΙΛΙΑ, ΔΙΑΛΕΚΤΟΣ, ΠΡΟΣΔΙΟΡΙΣΤΕ)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
            row,
        )

# Commit changes and close connection
conn.commit()
conn.close()

# Connect to the SQLite database
conn = sqlite3.connect('glossapi_database.db')

# Load data into a pandas DataFrame
df = pd.read_sql_query("SELECT * FROM glossapi_data", conn)

# Close the connection
conn.close()

# Display the first few rows of the DataFrame
print(df.head())

# Display information about the DataFrame
print(df.info())