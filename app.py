from flask import Flask, request, render_template, redirect, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
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
    return render_template('comm_det.html')

@app.route('/details/Business')
def business():
    return render_template("buss_det.html")

@app.route('/details/Business/deduct')
def bus_deduct():
    return render_template("page3.html")

@app.route('/details/Job')
def job_det():
    return render_template("Job_det.html")

@app.route('/details/Job/deduct')
def job_deduct():
    return render_template("job_deduct.html")


# PAN Validator
def PANno(PAN):
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(pattern, PAN))


# SIGNUP
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


# LOGIN
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


# COMMON DETAILS
@app.route('/details', methods=['POST'])
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

        cursor.execute('''
            INSERT INTO people_info 
            (name, fathers_guardian_name, date_of_birth, gender, email, aadhar_number, mobile_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (Name, Father, DOB, Gender, Email, Aadhar, Mobile))

        person_id = cursor.lastrowid

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

        flash("Details submitted successfully!")
        if category == "Business Person":
            return redirect(url_for("business"))
        elif category == "Job Person":
            return redirect(url_for("job_det"))
        else:
            flash("Please select a valid category")
            return redirect(url_for("details"))



# BUSINESS DETAILS
@app.route('/details/Business', methods=['POST'])
def businessdet():
    grin = request.form.get('gr-in')
    othin = request.form.get('oth-in')
    Bus = request.form.get('Bus')
    prname = request.form.get('pr-name')
    purprice = request.form.get('pur-price')
    purgst = request.form.get('pur-gst')
    tosp = request.form.get('tos-p')
    salprice = request.form.get('sal-price')
    sellgst = request.form.get('sell-gst')
    toss = request.form.get('tos-s')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO income_details(business_id, gross_income, other_income)
        VALUES(?,?,?)''', (Bus, grin, othin))

        cursor.execute('''INSERT INTO business_details(business_id, business_name, product_name, purchase_value, gst_rate_purchase, type_of_supply_purchase, sell_value, gst_rate_sell, type_of_supply_sell)
        VALUES(?,?,?,?,?,?,?,?,?)''', (Bus, Bus, prname, purprice, purgst, tosp, salprice, sellgst, toss))

    return redirect(url_for("bus_deduct"))


# JOB DETAILS
@app.route('/details/Job', methods=['POST'])
def jobdet():
    fin_y = request.form.get('financial_year')
    bas_sal = request.form.get('basic_salary')
    hra_rec = request.form.get('hra_received')
    sav_int = request.form.get('saving_interest')
    fd_int = request.form.get('fd_interest')
    oth_inc = request.form.get('other_income')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO job_details(financial_year, basic_salary, hra_received, interest_savings, interest_fd, other_income)
        VALUES(?,?,?,?,?,?)
        ''', (fin_y, bas_sal, hra_rec, sav_int, fd_int, oth_inc))

    flash("Job details submitted successfully!")
    return redirect(url_for("job_deduct"))


# JOB DEDUCTIONS
@app.route('/details/Job/deduct', methods=['POST'])
def jobdeduct():
    epf_ppf = request.form.get('epf_ppf')
    life_ins = request.form.get('life_insurance')
    elss = request.form.get('elss')
    home_loan_principal = request.form.get('home_loan_principal')
    tuition = request.form.get('tuition_fees')
    other_80c = request.form.get('other_80c')
    health_ins_self = request.form.get('health_insurance_self')
    health_ins_parents = request.form.get('health_insurance_parents')
    home_loan_interest = request.form.get('home_loan_interest')
    education_loan = request.form.get('education_loan_interest')
    donations = request.form.get('donations')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO job_deductions(section_80c_epf_ppf, section_80c_life_insurance, section_80c_elss_mutual_funds, section_80c_home_loan_principal, section_80c_childrens_tuition, section_80c_other_investments,
        section_80d_health_insurance_self_family, section_80d_health_insurance_parents, section_24_home_loan_interest_paid, section_80e_education_loan_interest_paid, section_80g_donations_charity)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ''', (epf_ppf, life_ins, elss, home_loan_principal, tuition, other_80c, health_ins_self, health_ins_parents, home_loan_interest, education_loan, donations))

        return redirect(url_for("index"))


# FINAL OUTPUT
@app.route('/index')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
