# reset_db.py
import sqlite3
import os

# Get project root (same logic as mydata_db.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_dir = os.path.join(BASE_DIR, 'database')
db_path = os.path.join(db_dir, 'mydata.db')

def reset_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Delete all data from tables
    cursor.execute("DELETE FROM user;")
    cursor.execute("DELETE FROM people_info;")
    cursor.execute("DELETE FROM job_person;")
    cursor.execute("DELETE FROM businesses;")
    cursor.execute("DELETE FROM income_details;")
    cursor.execute("DELETE FROM business_details;")
    cursor.execute("DELETE FROM job_details;")
    cursor.execute("DELETE FROM job_deductions;")

    # Reset auto-increment counters
    cursor.execute("DELETE FROM sqlite_sequence;")

    conn.commit()
    conn.close()
    print(f"✅ All tables cleared and auto-increment counters reset in {db_path}")

if __name__ == "__main__":
    reset_db()
