import os
import sqlite3
import re
from flask import Flask, request, render_template, redirect, flash, url_for, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai

# Import your custom calculation and PDF modules
from calc_job import calc_job_tax_new_regime 
from calc_bus import calc_bus_tax_new_regime 
from calc_gst import calculate_gst 
from pdf_gen import create_tax_report as create_job_report
from bus_pdf_gen import create_tax_report as create_business_report

# --- App Configuration ---
app = Flask(__name__)
app.secret_key = 'your_super_secret_key_12345'

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in .env file. AI features will be disabled.")

# --- Database Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database/mydata.db')

# --- Helper Function ---
def get_float(key):
    try:
        return float(request.form.get(key, 0) or 0)
    except (ValueError, TypeError):
        return 0.0

# ===================================================================
# --- General and User Management Routes ---
# ===================================================================
@app.route('/')
def landing():
    return render_template('landingpage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        pan = request.form.get('PAN')
        password = request.form.get('pass')
        if not pan or not password:
            flash("Please fill in all details!")
            return redirect(url_for('signup'))
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO user (PAN_ID, Password) VALUES (?, ?)', (pan, generate_password_hash(password)))
                conn.commit()
                flash("Signup successful! Please log in.")
                return redirect(url_for('signup'))
            except sqlite3.IntegrityError:
                flash("This PAN number is already registered.")
                return redirect(url_for('signup'))
    return render_template('sign-up.html')

@app.route('/login', methods=['POST'])
def login():
    pan = request.form.get('PAN')
    password = request.form.get('pass')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM user WHERE PAN_ID = ?', (pan,)).fetchone()
        if user and check_password_hash(user[2], password):
            flash("Login successful!")
            session.clear()
            session['pan_id'] = pan
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid PAN or password.")
            return redirect(url_for('signup'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.")
    return redirect(url_for('landing'))

# --- Dashboard and Category Selection ---
@app.route('/dashboard')
def dashboard():
    if 'pan_id' not in session:
        return redirect(url_for('signup'))
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        mapping = cursor.execute('SELECT person_id FROM user_pan_mapping WHERE pan_id = ?', (session['pan_id'],)).fetchone()
        if not mapping:
             return render_template('category.html')
        
        person_id = mapping[0]
        business_user = cursor.execute('SELECT 1 FROM businesses WHERE person_id = ?', (person_id,)).fetchone()
        if business_user:
            session['user_category'] = 'business'
            return redirect(url_for('dashboard_business'))
            
        job_user = cursor.execute('SELECT 1 FROM job_person WHERE person_id = ?', (person_id,)).fetchone()
        if job_user:
            session['user_category'] = 'job'
            return redirect(url_for('dashboard_job'))

    return render_template('category.html')

@app.route('/select_category', methods=['POST'])
def select_category():
    data = request.get_json()
    category = data.get('category')
    session['user_category'] = category
    return jsonify({'success': True, 'redirect': url_for('details')})

# --- Main Details Form ---
@app.route('/details', methods=['GET', 'POST'])
def details():
    if 'pan_id' not in session:
        return redirect(url_for('signup'))
        
    if request.method == 'POST':
        category = session.get('user_category')
        pan_id = session.get('pan_id')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("INSERT OR IGNORE INTO people_info (name, fathers_guardian_name, date_of_birth, gender, email, aadhar_number, mobile_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (request.form.get('name'), request.form.get('father'), request.form.get('dob'), request.form.get('gender'), request.form.get('email'), request.form.get('aadhar'), request.form.get('mno')))
            person = cursor.execute("SELECT id FROM people_info WHERE aadhar_number = ?", (request.form.get('aadhar'),)).fetchone()
            person_id = person[0] if person else None
            session['person_id'] = person_id

            if person_id:
                cursor.execute("INSERT OR IGNORE INTO user_pan_mapping (pan_id, person_id) VALUES (?, ?)", (pan_id, person_id))

            if category == "business":
                business_name = request.form.get('Bussname')
                cursor.execute("INSERT OR IGNORE INTO businesses (person_id, business_name) VALUES (?, ?)", (person_id, business_name))
                business = cursor.execute("SELECT id FROM businesses WHERE person_id = ?", (person_id,)).fetchone()
                if business:
                    session['business_id'] = business[0]
                conn.commit()
                return redirect(url_for("business_details"))

            elif category == "job":
                cursor.execute("INSERT OR IGNORE INTO job_person (person_id, employer_category, employer_tan_number) VALUES (?, ?, ?)",
                               (person_id, request.form.get('empc'), request.form.get('tan')))
                job_person = cursor.execute("SELECT id FROM job_person WHERE person_id = ?", (person_id,)).fetchone()
                if job_person:
                    session['job_person_id'] = job_person[0]
                conn.commit()
                return redirect(url_for("job_details"))
                
    return render_template('comm_det.html')

# ===================================================================
# --- Business User Workflow ---
# ===================================================================
@app.route('/business/details', methods=['GET', 'POST'])
def business_details():
    if request.method == 'POST':
        session['business_income'] = {
            'gross_income': get_float('gr-in'), 'other_income': get_float('oth-in'), 
            'total_income': get_float('gr-in') + get_float('oth-in')
        }
        session['business_details'] = {
            'business_name': request.form.get('Bus'), 'product_name': request.form.get('pr-name'),
            'purchase_value': get_float('pur-price'), 'gst_rate_purchase': get_float('pur-gst'), 
            'type_of_supply_purchase': request.form.get('tos-p'), 'sell_value': get_float('sal-price'), 
            'gst_rate_sell': get_float('sell-gst'), 'type_of_supply_sell': request.form.get('tos-s')
        }
        return redirect(url_for("business_expenses"))
    return render_template("buss_det.html")

@app.route('/business/expenses', methods=['GET', 'POST'])
def business_expenses():
    if request.method == 'POST':
        session['business_expenses'] = {
            'rent': get_float('rent'), 'employee_wage': get_float('emp-w'),
            'operating_expenses': get_float('op-exp'), 'subscription': get_float('sub'),
            'other_expenses': get_float('oth-expenses')
        }
        session['finance_deduction'] = {
            'section_80c': get_float('section-80c'), 'section_80d': get_float('section-80d'),
            'other_deduction': get_float('other-ded')
        }
        return redirect(url_for("business_result"))
    return render_template("buss_deduct.html")

@app.route('/business/result')
def business_result():
    required_keys = ['business_income', 'business_details', 'business_expenses', 'pan_id']
    if not all(key in session for key in required_keys):
        flash("Session data is missing. Please restart the calculation.")
        return redirect(url_for('business_details'))

    bus_income = session.get('business_income', {})
    bus_details = session.get('business_details', {})
    bus_expenses = session.get('business_expenses', {})
    fin_deductions = session.get('finance_deduction', {})
    
    gross_revenue = bus_income.get('total_income', 0)
    total_expenses = sum(bus_expenses.values())
    final_tax_payable, net_taxable_income = calc_bus_tax_new_regime(gross_revenue, total_expenses)

    gst_results = calculate_gst(
        bus_details.get('purchase_value', 0), int(bus_details.get('gst_rate_purchase', 0)),
        bus_details.get('type_of_supply_purchase', ''), bus_details.get('sell_value', 0),
        int(bus_details.get('gst_rate_sell', 0)), bus_details.get('type_of_supply_sell', '')
    )
    final_gst_payable = gst_results['net_payable']['total']

    insights = ""
    if GEMINI_API_KEY:
        try:
            prompt = f"Analyze this business data and provide 2-3 simple tax tips: Revenue ₹{gross_revenue:,.2f}, Expenses ₹{total_expenses:,.2f}, 80C Investment ₹{fin_deductions.get('section_80c', 0):,.2f}"
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            insights = response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            insights = "Could not generate AI insights at this time."

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tax_results_business (person_id, pan_id, business_id, gross_income, net_taxable_income, gst_payable, final_tax_payable, insights)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session.get('person_id'), session.get('pan_id'), session.get('business_id'), gross_revenue, net_taxable_income, final_gst_payable, final_tax_payable, insights))
        conn.commit()

    return render_template(
        "tax_result_bus.html",
        gross_income=round(gross_revenue, 2), net_taxable_income=round(net_taxable_income, 2),
        gst_payable=round(final_gst_payable, 2), final_tax_payable=round(final_tax_payable, 2),
        insights=insights
    )

# ===================================================================
# --- Job User Workflow ---
# ===================================================================
@app.route('/job/details', methods=['GET', 'POST'])
def job_details():
    if request.method == 'POST':
        session['job_income'] = {
            'financial_year': request.form.get('financial_year'), 'basic_salary': get_float('basic_salary'),
            'hra_received': get_float('hra_received'), 'savings_interest': get_float('savings_interest'),
            'fd_interest': get_float('fd_interest'), 'other_income': get_float('other_income')
        }
        return redirect(url_for("job_deductions"))
    return render_template("job_det.html")

@app.route('/job/deductions', methods=['GET', 'POST'])
def job_deductions():
    if request.method == 'POST':
        session['job_deductions'] = {
            'epf_ppf': get_float('epf_ppf'), 'life_ins': get_float('life_insurance'),
            'elss': get_float('elss'), 'home_loan_principal': get_float('home_loan_principal'),
            'tuition': get_float('tuition_fees'), 'other_80c': get_float('other_80c'),
            'health_ins_self': get_float('health_insurance_self'), 'health_ins_parents': get_float('health_insurance_parents'),
            'home_loan_interest': get_float('home_loan_interest'), 'education_loan_interest': get_float('education_loan_interest'),
            'donations': get_float('donations'), 'tds': get_float('tds')
        }
        return redirect(url_for("job_result"))
    return render_template("job_deduct.html")

@app.route('/job/result')
def job_result():
    if 'job_income' not in session or 'job_deductions' not in session:
        flash("Session data missing. Please restart the job calculation.")
        return redirect(url_for('job_details'))

    job_income = session.get('job_income', {})
    job_deductions = session.get('job_deductions', {})

    gross_income = sum(v for k, v in job_income.items() if k != 'financial_year')
    tds = job_deductions.get('tds', 0)
    final_tax_due, taxable_income = calc_job_tax_new_regime(gross_income, tds)

    insights = ""
    if GEMINI_API_KEY:
        try:
            section_80c_total = sum(job_deductions.get(k, 0) for k in ['epf_ppf', 'life_ins', 'elss', 'home_loan_principal', 'tuition', 'other_80c'])
            health_insurance_80d = job_deductions.get('health_ins_self', 0) + job_deductions.get('health_ins_parents', 0)
            
            prompt = f"Analyze this salaried employee's data and give 2-3 tax tips: Gross Salary ₹{gross_income:,.2f}, 80C Investments ₹{section_80c_total:,.2f}, 80D Health Insurance ₹{health_insurance_80d:,.2f}"
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            insights = response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            insights = "Could not generate AI insights at this time."

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tax_results_job (person_id, pan_id, financial_year, gross_income, tax, net_income, insights)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.get('person_id'), session.get('pan_id'), job_income.get('financial_year'),
            gross_income, final_tax_due, taxable_income, insights
        ))
        conn.commit()

    return render_template(
        "tax_result_job.html", 
        tax=round(final_tax_due, 2), 
        net_income=round(taxable_income, 2), 
        gross_income=round(gross_income, 2),
        insights=insights
    )

# ===================================================================
# --- Dashboard Routes (Corrected) ---
# ===================================================================
@app.route('/dashboard/business')
def dashboard_business():
    if 'pan_id' not in session:
        return redirect(url_for('signup'))
    
    pan_id = session.get('pan_id')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        history = cursor.execute('SELECT * FROM tax_results_business WHERE pan_id = ? ORDER BY created_at DESC', (pan_id,)).fetchall()
        
    history_for_template = [dict(row) for row in history]
    total_calculations = len(history_for_template)

    # Prepare chart data (chronological order)
    labels = [row['created_at'].split(' ')[0] for row in reversed(history_for_template)]
    revenue_data = [row['gross_income'] for row in reversed(history_for_template)]
    gst_data = [row['gst_payable'] for row in reversed(history_for_template)]
    tax_data = [row['final_tax_payable'] for row in reversed(history_for_template)]

    return render_template(
        'dash_bus.html',
        history=history_for_template,
        pan_number=pan_id,
        total_calculations=total_calculations,
        labels=labels,
        revenue_data=revenue_data,
        gst_data=gst_data,
        tax_data=tax_data
    )

@app.route('/dashboard/job')
def dashboard_job():
    if 'pan_id' not in session:
        return redirect(url_for('signup'))
        
    pan_id = session.get('pan_id')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        history = cursor.execute('SELECT * FROM tax_results_job WHERE pan_id = ? ORDER BY created_at DESC', (pan_id,)).fetchall()
        
    history_for_template = [dict(row) for row in history]
    total_calculations = len(history_for_template)

    # Prepare chart data (chronological order)
    labels = [row['financial_year'] for row in reversed(history_for_template)]
    gross_income_data = [row['gross_income'] for row in reversed(history_for_template)]
    tax_data = [row['tax'] for row in reversed(history_for_template)]
    net_income_data = [row['net_income'] for row in reversed(history_for_template)]

    return render_template(
        'dash_job.html',
        history=history_for_template,
        pan_number=pan_id,
        total_calculations=total_calculations,
        labels=labels,
        gross_income_data=gross_income_data,
        tax_data=tax_data,
        net_income_data=net_income_data
    )

# ===================================================================
# --- PDF Download Routes ---
# ===================================================================
@app.route('/download-business-report')
def download_business_report():
    required_keys = ['person_id', 'business_income', 'business_details', 'business_expenses', 'finance_deduction']
    if not all(key in session for key in required_keys):
        flash("Session expired. Please fill out business forms again to download.")
        return redirect(url_for('details'))

    person_id = session.get('person_id')
    personal_details = {}
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        user_data = cursor.execute("SELECT name, email, mobile_number FROM people_info WHERE id = ?", (person_id,)).fetchone()
        if user_data:
            personal_details = dict(user_data)

    bus_income = session.get('business_income', {})
    bus_details = session.get('business_details', {})
    bus_expenses = session.get('business_expenses', {})
    fin_deductions = session.get('finance_deduction', {})

    total_revenue = bus_income.get('total_income', 0)
    total_expenses = sum(bus_expenses.values())
    
    final_tax_due, taxable_income = calc_bus_tax_new_regime(total_revenue, total_expenses)

    data_for_pdf = {
        'personal': personal_details,
        'income': {**bus_income, **bus_details},
        'gst': bus_details,
        'expenses': {**bus_expenses, **fin_deductions},
        'summary': {'taxable_income': taxable_income, 'final_tax_due': final_tax_due}
    }
    
    pdf_buffer = create_business_report(data_for_pdf)

    return send_file(pdf_buffer, as_attachment=True, download_name='Business_Tax_Report.pdf', mimetype='application/pdf')

@app.route('/download-job-report')
def download_job_report():
    required_keys = ['person_id', 'job_income', 'job_deductions']
    if not all(key in session for key in required_keys):
        flash("Session expired. Please fill out job forms again to download.")
        return redirect(url_for('details'))
    
    person_id = session.get('person_id')
    personal_details = {}
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        user_data = cursor.execute("SELECT name, email, mobile_number FROM people_info WHERE id = ?", (person_id,)).fetchone()
        if user_data:
            personal_details = dict(user_data)

    job_income = session.get('job_income', {})
    job_deductions = session.get('job_deductions', {})

    gross_income = sum(v for k, v in job_income.items() if k != 'financial_year')
    tds = job_deductions.get('tds', 0)
    final_tax_due, taxable_income = calc_job_tax_new_regime(gross_income, tds)
    
    data_for_pdf = {
        'personal': personal_details,
        'income': job_income,
        'deductions': job_deductions,
        'summary': {
            'gross_income': gross_income,
            'taxable_income': taxable_income,
            'final_tax_due': final_tax_due
        }
    }

    pdf_buffer = create_job_report(data_for_pdf)
    return send_file(pdf_buffer, as_attachment=True, download_name='Job_Tax_Report.pdf', mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)

