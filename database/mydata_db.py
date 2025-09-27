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

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS income_details (
        detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER,
        gross_income REAL,
        other_income REAL,
        FOREIGN KEY(business_id) REFERENCES businesses(id)
    )
    ''')


    cursor.execute('''
    CREATE TABLE IF NOT EXISTS business_details (
        business_id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT,
        product_name TEXT,
        purchase_value REAL,
        gst_rate_purchase TEXT,
        type_of_supply_purchase TEXT,
        sell_value REAL,
        gst_rate_sell TEXT,
        type_of_supply_sell TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER,
        financial_year TEXT,
        basic_salary REAL,
        hra_received REAL,
        interest_savings REAL,
        interest_fd REAL,
        other_income REAL,
        FOREIGN KEY(person_id) REFERENCES job_person(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_deductions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_id INTEGER,
        section_80c_epf_ppf REAL,
        section_80c_life_insurance REAL,
        section_80c_elss_mutual_funds REAL,
        section_80c_home_loan_principal REAL,
        section_80c_childrens_tuition REAL,
        section_80c_other_investments REAL,
        section_80d_health_insurance_self_family REAL,
        section_80d_health_insurance_parents REAL,
        section_24_home_loan_interest_paid REAL,
        section_80e_education_loan_interest_paid REAL,
        section_80g_donations_charity REAL,
        tds REAL,
        FOREIGN KEY(person_id) REFERENCES job_person(id)
    )
    ''')


    conn.commit()
    conn.close()
    print(f"✅ All tables created successfully in {db_path}")

if __name__ == "__main__":
    init_db()
