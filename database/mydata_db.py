# mydata_db.py
import sqlite3
import os

# Get project root (parent of this file’s folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database folder (only one level)
db_dir = os.path.join(BASE_DIR, 'database')
os.makedirs(db_dir, exist_ok=True)

# Database file
db_path = os.path.join(db_dir, 'mydata.db')

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # User Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        PAN_ID VARCHAR(50) NOT NULL UNIQUE,
        Password VARCHAR(50) NOT NULL
    )
    ''')

    # People Info Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS people_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        fathers_guardian_name TEXT,
        date_of_birth DATE,
        gender TEXT,
        email TEXT,
        aadhar_number TEXT,
        mobile_number TEXT
    )
    ''')

    # Job Person
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_person (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER,
        employer_category TEXT,
        employer_tan_number TEXT,
        FOREIGN KEY(person_id) REFERENCES people_info(id)
    )
    ''')

    # Businesses
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER,
        business_name TEXT,
        date_of_gst_registration DATE,
        gstin TEXT,
        nature_of_business TEXT,
        FOREIGN KEY(person_id) REFERENCES people_info(id)
    )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ All tables created successfully in {db_path}")

if __name__ == "__main__":
    init_db()
