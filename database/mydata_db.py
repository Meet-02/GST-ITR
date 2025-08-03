# init_db.py
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'mydata.db')
conn = sqlite3.connect(db_path)

conn.execute('''
CREATE TABLE IF NOT EXISTS user (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PAN_ID VARCHAR(50) NOT NULL UNIQUE,
    Password VARCHAR(50) NOT NULL
)
''')

conn.commit()
conn.close()
print("Table created successfully.")
