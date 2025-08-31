from flask import Flask, request, render_template, redirect, flash, url_for
from werkzeug.security import generate_password_hash,check_password_hash
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Absolute base dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database/mydata.db')

@app.route('/')
def landing():
    return render_template('landingpage.html')

@app.route('/signup')
def sign_up():
    return render_template('sign-up.html')

@app.route('/details')
def details():
    return render_template('page1.html')

@app.route('/details/Business')
def business():
    return render_template("page2.html")

def PANno(PAN):
    a = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(a, PAN))

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('name')
    pan = request.form.get('PAN')
    password = request.form.get('pass')

    if not username or not pan or not password:
        flash("Please fill up all your details !!")
        return redirect(url_for('sign_up')) 

    if not PANno(pan):
        flash("Invalid PAN number")
        return redirect(url_for('sign_up')) 

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO user (PAN_ID, Password) VALUES (?, ?)', (pan, generate_password_hash(password)))
            conn.commit()
            flash("Signup successful")
            return redirect(url_for('common_details'))
        except sqlite3.IntegrityError:
            flash("PAN number already exists")
            return render_template('sign-up.html') 

@app.route('/login', methods=['POST'])
def login():
    pan = request.form.get('PAN')
    password = request.form.get('pass')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE PAN_ID = ?', (pan,))
        user = cursor.fetchone()

        if user:
            stored_hash = user[2]  
            if check_password_hash(stored_hash, password):
                flash("Login successful")
                return redirect(url_for('common_details'))
            else:
                flash("Invalid password")
        else:
            flash("Invalid PAN number")

    return render_template('sign-up.html')

@app.route('/details' ,methods = ['POST'])
def common_details():
    Name = request.form.get('name')
    Father = request.form.get('father')
    DOB = request.form.get('dob')
    Gender = request.form.get('gender')
    Email = request.form.get('email')
    Aadhar = request.form.get('aadhar')
    Mobile = request.form.get('mno')
    category = request.form.get('userType')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Insert into people_info
        cursor.execute('''
            INSERT INTO people_info 
            (name, fathers_guardian_name, date_of_birth, gender, email, aadhar_number, mobile_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (Name, Father, DOB, Gender, Email, Aadhar, Mobile))

        person_id = cursor.lastrowid   # get the new person id

        # Insert into job_person or businesses based on category
        if category == "Job Person":
            employer_category = request.form.get('empc')
            employer_tan = request.form.get('tan')

            cursor.execute('''
                INSERT INTO job_person (person_id, employer_category, employer_tan_number)
                VALUES (?, ?, ?)
            ''', (person_id, employer_category, employer_tan))

        
        elif category == "Business Person":
            business_name = request.form.get('Bussname')
            gst_date = request.form.get('DOR')
            gstin = request.form.get('GSTIN')
            nature = request.form.get('nob')

            cursor.execute('''
                INSERT INTO businesses (person_id, business_name, date_of_gst_registration, gstin, nature_of_business)
                VALUES (?, ?, ?, ?, ?)
            ''', (person_id, business_name, gst_date, gstin, nature))

        conn.commit()

        flash("Details submitted successfully!")
        if category == "Business Person":
            return redirect(url_for("business"))
        elif category == "Job Person":
            return redirect(url_for("index"))

@app.route('/details/Job')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
