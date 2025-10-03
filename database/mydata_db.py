import sqlite3
import os

# Get project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_dir = os.path.join(BASE_DIR, 'database')
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'mydata.db')

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # --- User and Profile Tables ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        PAN_ID VARCHAR(50) NOT NULL UNIQUE,
        Password VARCHAR(255) NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS people_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, fathers_guardian_name TEXT, date_of_birth DATE,
        gender TEXT, email TEXT, aadhar_number TEXT UNIQUE, mobile_number TEXT
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_pan_mapping (
        pan_id TEXT PRIMARY KEY,
        person_id INTEGER,
        FOREIGN KEY (person_id) REFERENCES people_info(id)
    )''')
    
    # --- Business Tables ---
    cursor.execute("DROP TABLE IF EXISTS businesses")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER, business_name TEXT,
        FOREIGN KEY(person_id) REFERENCES people_info(id)
    )''')

    # --- Job Tables ---
    cursor.execute("DROP TABLE IF EXISTS job_person")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_person (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER,
        FOREIGN KEY(person_id) REFERENCES people_info(id)
    )''')

    # --- Tax Results History Tables (Cleaned Up) ---
    cursor.execute('DROP TABLE IF EXISTS tax_results_job')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tax_results_job (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL, pan_id TEXT NOT NULL, financial_year TEXT,
        gross_income REAL, tax REAL, net_income REAL, insights TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('DROP TABLE IF EXISTS tax_results_business')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tax_results_business (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER NOT NULL, pan_id TEXT NOT NULL, business_id INTEGER,
        gross_income REAL, net_taxable_income REAL, gst_payable REAL,
        final_tax_payable REAL, insights TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    print(f"Database and all tables created successfully in {db_path}")

if __name__ == "__main__":
    init_db()

