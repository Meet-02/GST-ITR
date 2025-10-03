# import sqlite3
# import os

# # This correctly points to the folder containing this script
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# # This now correctly points to the database file in the same folder
# db_path = os.path.join(BASE_DIR, "mydata.db")

# conn = sqlite3.connect(db_path)
# cursor = conn.cursor()

# try:
#     # This command adds the 'tds' column if it doesn't exist
#     cursor.execute("ALTER TABLE income_details ADD COLUMN Total_revenue REAL;")
#     print("✅ Column 'Total_revenue' added successfully!")
# except sqlite3.OperationalError as e:
#     # This will catch errors, including if the column already exists
#     print(f"⚠️  Error: {e}")

# conn.commit()
# conn.close()


import sqlite3
import os

# This correctly points to the folder containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# This now correctly points to the database file in the same folder
db_path = os.path.join(BASE_DIR, "mydata.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add created_at column if missing
try:
    cursor.execute("ALTER TABLE tax_results_job ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
except sqlite3.OperationalError:
    print("Column 'created_at' already exists in tax_results_job")

try:
    cursor.execute("ALTER TABLE tax_results_business ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;")
except sqlite3.OperationalError:
    print("Column 'created_at' already exists in tax_results_business")

# Add missing columns to job_person
try:
    cursor.execute("ALTER TABLE job_person ADD COLUMN employer_category TEXT;")
except sqlite3.OperationalError:
    print("Column 'employer_category' already exists in job_person")

try:
    cursor.execute("ALTER TABLE job_person ADD COLUMN employer_tan_number TEXT;")
except sqlite3.OperationalError:
    print("Column 'employer_tan_number' already exists in job_person")

conn.commit()
conn.close()
print("Schema upgrade complete")














import sqlite3
import os

# Get project root (parent of this file’s folder) - RESTORED TO YOUR ORIGINAL METHOD
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database folder (only one level)
db_dir = os.path.join(BASE_DIR, 'database')
os.makedirs(db_dir, exist_ok=True)

# Database file
db_path = os.path.join(db_dir, 'mydata.db')