import sqlite3
import os

# This correctly points to the folder containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# This now correctly points to the database file in the same folder
db_path = os.path.join(BASE_DIR, "mydata.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # This command adds the 'tds' column if it doesn't exist
    cursor.execute("ALTER TABLE income_details ADD COLUMN Total_revenue REAL;")
    print("✅ Column 'Total_revenue' added successfully!")
except sqlite3.OperationalError as e:
    # This will catch errors, including if the column already exists
    print(f"⚠️  Error: {e}")

conn.commit()
conn.close()