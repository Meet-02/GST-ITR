
import os
import sqlite3
import re
from flask import Flask, request, render_template, redirect, flash, url_for, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai

# Import your custom calculation and PDF modules
# Make sure your files are named correctly, e.g., calc_job.py, calc_bus.py, etc.
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

# Configure the Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in .env file. AI features will be disabled.")

# --- Database Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database/mydata.db')

# --- Helper Functions ---
def get_float(key):
    try:
        return float(request.form.get(key, 0) or 0)
    except (ValueError, TypeError):
        return 0.0

# --- General and User Management Routes ---
@app.route('/')
def landing():
    return render_template('landingpage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        pan = request.form.get('PAN')
        password = request.form.get('pass')
        if not pan or not password:
            flash("Please fill all details!")
            return redirect(url_for('signup'))

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO user (PAN_ID, Password) VALUES (?, ?)', (pan, generate_password_hash(password)))
                conn.commit()
                flash("Signup successful! Please log in.")
                return redirect(url_for('signup'))
            except sqlite3.IntegrityError:
                flash("PAN number already exists")
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
            flash("Login successful")
            session.clear() # Clear any old data on a new login
            session['pan_id'] = pan
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid PAN or password")
            return redirect(url_for('signup'))

@app.route('/category')
def category():
    return render_template('category.html')

@app.route('/select_category', methods=['POST'])
def select_category():
    data = request.get_json()
    category = data.get('category')
    session['user_category'] = category
    return jsonify({'success': True, 'redirect': url_for('details')})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    pan_id = session.get('pan_id')
    if not pan_id:
        return redirect(url_for('signup'))

    # Check if user has completed setup
    if not session.get('user_category') or not session.get('person_id'):
        return redirect(url_for('category'))

    # Redirect to appropriate dashboard based on category
    category = session.get('user_category')
    if category == 'business':
        return redirect(url_for('dashboard_business'))
    elif category == 'job':
        return redirect(url_for('dashboard_job'))
    else:
        return redirect(url_for('category'))

@app.route('/details', methods=['GET', 'POST'])
def details():
    if request.method == 'POST':
        Name = request.form.get('name')
        Father = request.form.get('father')
        DOB = request.form.get('dob')
        Gender = request.form.get('gender')
        Email = request.form.get('email')
        Aadhar = request.form.get('aadhar')
        Mobile = request.form.get('mno')
        category = session.get('user_category')

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if PAN already has a person mapping
            pan_id = session.get('pan_id')
            existing_mapping = cursor.execute('SELECT person_id FROM user_pan_mapping WHERE pan_id = ?', (pan_id,)).fetchone()

            if existing_mapping:
                # Use existing person_id
                person_id = existing_mapping[0]
                session['person_id'] = person_id
                # Update existing person info
                cursor.execute('UPDATE people_info SET name = ?, fathers_guardian_name = ?, date_of_birth = ?, gender = ?, email = ?, aadhar_number = ?, mobile_number = ? WHERE id = ?',
                              (Name, Father, DOB, Gender, Email, Aadhar, Mobile, person_id))
            else:
                # Create new person
                cursor.execute('INSERT INTO people_info (name, fathers_guardian_name, date_of_birth, gender, email, aadhar_number, mobile_number) VALUES (?, ?, ?, ?, ?, ?, ?)', (Name, Father, DOB, Gender, Email, Aadhar, Mobile))
                person_id = cursor.lastrowid
                session['person_id'] = person_id
                # Link PAN to person
                cursor.execute('INSERT INTO user_pan_mapping (pan_id, person_id) VALUES (?, ?)', (pan_id, person_id))

            if category == "business":
                # Check if business already exists for this person
                existing_business = cursor.execute('SELECT id FROM businesses WHERE person_id = ?', (person_id,)).fetchone()
                if existing_business:
                    session['business_id'] = existing_business[0]
                    # Update business info
                    business_name = request.form.get('Bussname')
                    gst_registration_date = request.form.get('DOR')
                    gstin = request.form.get('GSTIN')
                    nature_of_business = request.form.get('nob')
                    cursor.execute('UPDATE businesses SET business_name = ?, date_of_gst_registration = ?, gstin = ?, nature_of_business = ? WHERE id = ?',
                                  (business_name, gst_registration_date, gstin, nature_of_business, existing_business[0]))
                else:
                    business_name = request.form.get('Bussname')
                    gst_registration_date = request.form.get('DOR')
                    gstin = request.form.get('GSTIN')
                    nature_of_business = request.form.get('nob')
                    cursor.execute('INSERT INTO businesses (person_id, business_name, date_of_gst_registration, gstin, nature_of_business) VALUES (?, ?, ?, ?, ?)', (person_id, business_name, gst_registration_date, gstin, nature_of_business))
                    session['business_id'] = cursor.lastrowid
                conn.commit()
                return redirect(url_for("business"))
            elif category == "job":
                # Check if job_person already exists for this person
                existing_job_person = cursor.execute('SELECT id FROM job_person WHERE person_id = ?', (person_id,)).fetchone()
                if existing_job_person:
                    session['job_person_id'] = existing_job_person[0]
                    # Update job person info
                    employer_category = request.form.get('empc')
                    employer_tan = request.form.get('tan')
                    cursor.execute('UPDATE job_person SET employer_category = ?, employer_tan_number = ? WHERE id = ?',
                                  (employer_category, employer_tan, existing_job_person[0]))
                else:
                    employer_category = request.form.get('empc')
                    employer_tan = request.form.get('tan')
                    cursor.execute('INSERT INTO job_person (person_id, employer_category, employer_tan_number) VALUES (?, ?, ?)', (person_id, employer_category, employer_tan))
                    session['job_person_id'] = cursor.lastrowid
                conn.commit()
                return redirect(url_for("job_det"))

    return render_template('comm_det.html')


# ===================================================================
# --- Business User Workflow ---
# ===================================================================
@app.route('/details/Business')
def business():
    return render_template("buss_det.html")

@app.route('/details/Business', methods=['POST'])
def businessdet():
    grin = get_float('gr-in')
    othin = get_float('oth-in')
    total_rev = grin + othin

    session['business_income'] = {
        'gross_income': grin,
        'other_income': othin,
        'total_income': total_rev
    }
    session['business_details'] = {
        'business_name': request.form.get('Bus'),
        'product_name': request.form.get('pr-name'),
        'purchase_value': get_float('pur-price'),
        'gst_rate_purchase': get_float('pur-gst'),
        'type_of_supply_purchase': request.form.get('tos-p'),
        'sell_value': get_float('sal-price'),
        'gst_rate_sell': get_float('sell-gst'),
        'type_of_supply_sell': request.form.get('tos-s')
    }

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        business_id = session.get('business_id')
        bus_details = session.get('business_details', {})

        # Check if income_details already exists for this business
        existing_income = cursor.execute('SELECT id FROM income_details WHERE business_id = ?', (business_id,)).fetchone()
        if existing_income:
            cursor.execute('''UPDATE income_details SET gross_income = ?, other_income = ?, Total_revenue = ? WHERE business_id = ?''',
                          (grin, othin, total_rev, business_id))
        else:
            cursor.execute('''INSERT INTO income_details(business_id, gross_income, other_income, Total_revenue)
            VALUES(?,?,?,?)''', (business_id, grin, othin, total_rev))

        # Check if business_details already exists for this business
        existing_details = cursor.execute('SELECT id FROM business_details WHERE business_id = ?', (business_id,)).fetchone()
        if existing_details:
            cursor.execute('''UPDATE business_details SET business_name = ?, product_name = ?, purchase_value = ?, gst_rate_purchase = ?, type_of_supply_purchase = ?, sell_value = ?, gst_rate_sell = ?, type_of_supply_sell = ? WHERE business_id = ?''',
                          (bus_details.get('business_name'), bus_details.get('product_name'), bus_details.get('purchase_value'), bus_details.get('gst_rate_purchase'), bus_details.get('type_of_supply_purchase'), bus_details.get('sell_value'), bus_details.get('gst_rate_sell'), bus_details.get('type_of_supply_sell'), business_id))
        else:
            cursor.execute('''INSERT INTO business_details(business_id, business_name, product_name, purchase_value, gst_rate_purchase, type_of_supply_purchase, sell_value, gst_rate_sell, type_of_supply_sell)
            VALUES(?,?,?,?,?,?,?,?,?)''', (business_id, bus_details.get('business_name'), bus_details.get('product_name'), bus_details.get('purchase_value'), bus_details.get('gst_rate_purchase'), bus_details.get('type_of_supply_purchase'), bus_details.get('sell_value'), bus_details.get('gst_rate_sell'), bus_details.get('type_of_supply_sell')))
        conn.commit()

    return redirect(url_for("bus_deduct"))

@app.route('/details/Business/deduct')
def bus_deduct():
    return render_template("buss_deduct.html")

@app.route('/details/Business/deduct', methods=['POST'])
def bussdeduct():
    rent = get_float('rent')
    emp_w = get_float('emp-w')
    Bus_op = get_float('op-exp')
    sub = get_float('sub')
    oth = get_float('oth-expenses')
    section80c = get_float('section-80c')
    section80d = get_float('section-80d')
    other_deduction = get_float('other-ded')

    session['business_expenses'] = {
        'rent': rent,
        'employee_wage': emp_w,
        'operating_expenses': Bus_op,
        'subscription': sub,
        'other_expenses': oth
    }
    session['finance_deduction'] = {
        'section_80c': section80c,
        'section_80d': section80d,
        'other_deduction': other_deduction
    }

    # --- Database insertion/update for expenses and deductions ---
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check if business_expenses already exists (assuming one per business for simplicity)
        existing_expenses = cursor.execute('SELECT rowid FROM business_expenses LIMIT 1').fetchone()
        if existing_expenses:
            cursor.execute('''
                UPDATE business_expenses SET rent = ?, employee_wage = ?, operating_expenses = ?, subscription = ?, other_expenses = ?
                WHERE rowid = ?
            ''', (rent, emp_w, Bus_op, sub, oth, existing_expenses[0]))
        else:
            cursor.execute('''
                INSERT INTO business_expenses (rent, employee_wage, operating_expenses, subscription, other_expenses)
                VALUES (?, ?, ?, ?, ?)
            ''', (rent, emp_w, Bus_op, sub, oth))

        # Check if finance_deduction already exists
        existing_deductions = cursor.execute('SELECT rowid FROM finance_deduction LIMIT 1').fetchone()
        if existing_deductions:
            cursor.execute('''
                UPDATE finance_deduction SET section_80c = ?, section_80d = ?, other_deduction = ?
                WHERE rowid = ?
            ''', (section80c, section80d, other_deduction, existing_deductions[0]))
        else:
            cursor.execute('''
                INSERT INTO finance_deduction (section_80c, section_80d, other_deduction)
                VALUES (?, ?, ?)
            ''', (section80c, section80d, other_deduction))
        conn.commit()

    return redirect(url_for("bus_result"))

@app.route('/details/Business/result')
def bus_result():
    required_keys = ['business_income', 'business_details', 'business_expenses']
    if not all(key in session for key in required_keys):
        flash("Session data is missing. Please restart the business calculation.")
        return redirect(url_for('business'))

    bus_income = session.get('business_income', {})
    bus_details = session.get('business_details', {})
    bus_expenses = session.get('business_expenses', {})
    fin_deductions = session.get('finance_deduction', {})
    
    # ITR Calculation
    gross_revenue = bus_income.get('total_income', 0)
    total_expenses = sum(bus_expenses.values())
    final_tax_payable, net_taxable_income = calc_bus_tax_new_regime(gross_revenue, total_expenses)

    # GST Calculation
    gst_results = calculate_gst(
        bus_details.get('purchase_value', 0), int(bus_details.get('gst_rate_purchase', 0)),
        bus_details.get('type_of_supply_purchase', ''), bus_details.get('sell_value', 0),
        int(bus_details.get('gst_rate_sell', 0)), bus_details.get('type_of_supply_sell', '')
    )
    final_gst_payable = gst_results['net_payable']['total']

    # AI Insights Generation
    insights = ""
    if GEMINI_API_KEY:
        try:
            prompt = f"""
            You are a helpful Indian tax-saving assistant. Analyze this business owner's data and provide 2-3 simple, actionable tax tips in bullet points.

            **User's Data:**
            - Total Revenue: ₹{gross_revenue:,.2f}
            - Total Business Expenses: ₹{total_expenses:,.2f}
            - 80C Investment: ₹{fin_deductions.get('section_80c', 0):,.2f}
            """
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            insights = response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            insights = "Could not generate AI insights at this time."

    # Save to database
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tax_results_business (person_id, pan_id, business_id, gross_income, net_taxable_income, gst_payable, final_tax_payable, insights)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session.get('person_id'), session.get('pan_id'), session.get('business_id'), gross_revenue, net_taxable_income, final_gst_payable, final_tax_payable, insights))
        conn.commit()

    return render_template(
        "tax_result_bus.html",
        gross_income=round(gross_revenue, 2),
        net_taxable_income=round(net_taxable_income, 2),
        gst_payable=round(final_gst_payable, 2),
        final_tax_payable=round(final_tax_payable, 2),
        insights=insights
    )

# ===================================================================
# --- Job User Workflow ---
# ===================================================================
@app.route('/details/Job')
def job_det():
    return render_template("Job_det.html")

@app.route('/details/Job', methods=['POST'])
def jobdet():
    session['job_income'] = {
        'financial_year': request.form.get('financial_year'),
        'basic_salary': get_float('basic_salary'),
        'hra_received': get_float('hra_received'),
        'savings_interest': get_float('savings_interest'),
        'fd_interest': get_float('fd_interest'),
        'other_income': get_float('other_income')
    }
    # DB insert/update for job details
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        job_income = session.get('job_income')
        job_person_id = session.get('job_person_id')

        # Check if job_details already exists for this job_person
        existing_details = cursor.execute('SELECT id FROM job_details WHERE person_id = ?', (job_person_id,)).fetchone()
        if existing_details:
            cursor.execute('''
                UPDATE job_details SET financial_year = ?, basic_salary = ?, hra_received = ?, interest_savings = ?, interest_fd = ?, other_income = ?
                WHERE person_id = ?
            ''', (job_income['financial_year'], job_income['basic_salary'], job_income['hra_received'], job_income['savings_interest'], job_income['fd_interest'], job_income['other_income'], job_person_id))
        else:
            cursor.execute('''
                INSERT INTO job_details (person_id, financial_year, basic_salary, hra_received, interest_savings, interest_fd, other_income)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (job_person_id, job_income['financial_year'], job_income['basic_salary'], job_income['hra_received'], job_income['savings_interest'], job_income['fd_interest'], job_income['other_income']))
        conn.commit()
    return redirect(url_for("job_deduct"))

@app.route('/details/Job/deduct')
def job_deduct():
    return render_template("job_deduct.html")

@app.route('/details/Job/deduct', methods=['POST'])
def jobdeduct():
    session['job_deductions'] = {
        'epf_ppf': get_float('epf_ppf'),
        'life_ins': get_float('life_insurance'),
        'elss': get_float('elss'),
        'home_loan_principal': get_float('home_loan_principal'),
        'tuition': get_float('tuition_fees'),
        'other_80c': get_float('other_80c'),
        'health_ins_self': get_float('health_insurance_self'),
        'health_ins_parents': get_float('health_insurance_parents'),
        'home_loan_interest': get_float('home_loan_interest'),
        'education_loan_interest': get_float('education_loan_interest'),
        'donations': get_float('donations'),
        'tds': get_float('tds')
    }
    # DB insert/update for job deductions
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        job_deductions = session.get('job_deductions')
        job_person_id = session.get('job_person_id')

        # Check if job_deductions already exists for this job_person
        existing_deductions = cursor.execute('SELECT id FROM job_deductions WHERE person_id = ?', (job_person_id,)).fetchone()
        if existing_deductions:
            cursor.execute('''
                UPDATE job_deductions SET section_80c_epf_ppf = ?, section_80c_life_insurance = ?, section_80c_elss_mutual_funds = ?, section_80c_home_loan_principal = ?, section_80c_childrens_tuition = ?, section_80c_other_investments = ?, section_80d_health_insurance_self_family = ?, section_80d_health_insurance_parents = ?, section_24_home_loan_interest_paid = ?, section_80e_education_loan_interest_paid = ?, section_80g_donations_charity = ?, tds = ?
                WHERE person_id = ?
            ''', (job_deductions['epf_ppf'], job_deductions['life_ins'], job_deductions['elss'], job_deductions['home_loan_principal'], job_deductions['tuition'], job_deductions['other_80c'], job_deductions['health_ins_self'], job_deductions['health_ins_parents'], job_deductions['home_loan_interest'], job_deductions['education_loan_interest'], job_deductions['donations'], job_deductions['tds'], job_person_id))
        else:
            cursor.execute('''
                INSERT INTO job_deductions (person_id, section_80c_epf_ppf, section_80c_life_insurance, section_80c_elss_mutual_funds, section_80c_home_loan_principal, section_80c_childrens_tuition, section_80c_other_investments, section_80d_health_insurance_self_family, section_80d_health_insurance_parents, section_24_home_loan_interest_paid, section_80e_education_loan_interest_paid, section_80g_donations_charity, tds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_person_id, job_deductions['epf_ppf'], job_deductions['life_ins'], job_deductions['elss'], job_deductions['home_loan_principal'], job_deductions['tuition'], job_deductions['other_80c'], job_deductions['health_ins_self'], job_deductions['health_ins_parents'], job_deductions['home_loan_interest'], job_deductions['education_loan_interest'], job_deductions['donations'], job_deductions['tds']))
        conn.commit()
    return redirect(url_for("job_result"))

@app.route('/details/Job/result')
def job_result():
    job_income = session.get('job_income', {})
    job_deductions = session.get('job_deductions', {})

    # --- Income & Deductions ---
    gross_income = sum(v for k, v in job_income.items() if k != 'financial_year')
    deductions = sum(job_deductions.values())
    tds = job_deductions.get('tds', 0)

    # --- Tax Calculation ---
    final_tax_due, taxable_income = calc_job_tax_new_regime(gross_income, tds)
    net_income = taxable_income
    tax = final_tax_due

    # --- AI Insights ---
    insights = ""
    if GEMINI_API_KEY:
        try:
            section_80c_total = sum(
                job_deductions.get(k, 0)
                for k in ['epf_ppf', 'life_ins', 'elss', 'home_loan_principal', 'tuition', 'other_80c']
            )
            health_insurance_80d = (
                job_deductions.get('health_ins_self', 0)
                + job_deductions.get('health_ins_parents', 0)
            )

            prompt = f"""
            You are a helpful Indian tax-saving assistant. Analyze this salaried employee's data and provide 2-3 simple, actionable tax tips.
            - Gross Salary: ₹{gross_income:,.2f}
            - 80C Investments: ₹{section_80c_total:,.2f}
            - 80D Health Insurance: ₹{health_insurance_80d:,.2f}
            - Total Deductions: ₹{deductions:,.2f}
            - Final Tax Payable: ₹{tax:,.2f}
            """
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            insights = response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            insights = "Could not generate AI insights at this time."

    # --- Save Current Result ---
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tax_results_job 
            (person_id, pan_id, financial_year, gross_income, tax, net_income, insights)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.get('person_id'),
            session.get('pan_id'),
            job_income.get('financial_year'),
            gross_income,
            tax,
            net_income,
            insights
        ))
        conn.commit()

        # --- Fetch ALL history for charts ---
        cursor.execute('''
            SELECT financial_year, gross_income, tax, net_income, insights, created_at
            FROM tax_results_job
            WHERE person_id=? AND pan_id=?
            ORDER BY created_at DESC
        ''', (session.get('person_id'), session.get('pan_id')))
        rows = cursor.fetchall()

    # --- Prepare history & chart data ---
    history = []
    labels, gross_income_data, tax_data, net_income_data = [], [], [], []

    for r in rows:
        hist_entry = {
            "financial_year": r[0],
            "gross_income": r[1],
            "tax": r[2],
            "net_income": r[3],
            "insights": r[4],
            "date": r[5]
        }
        history.append(hist_entry)

        labels.append(r[0])
        gross_income_data.append(r[1])
        tax_data.append(r[2])
        net_income_data.append(r[3])

    total_calculations = len(history)

    # --- Send everything to dashboard ---
    return render_template(
        "dash_job.html",
        gross_income=gross_income,
        deductions=deductions,
        net_income=net_income,
        tax=tax,
        insights=insights,
        history=history,
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

# ===================================================================
# --- Dashboard Routes ---
# ===================================================================
@app.route('/dashboard/business')
def dashboard_business():
    pan_id = session.get('pan_id')
    if not pan_id:
        return redirect(url_for('signup'))

    # Check if user has completed setup
    if not session.get('user_category') or not session.get('person_id'):
        return redirect(url_for('category'))
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        history = cursor.execute('SELECT gross_income, net_taxable_income, gst_payable, final_tax_payable, insights, created_at as date FROM tax_results_business WHERE pan_id = ? ORDER BY created_at DESC', (pan_id,)).fetchall()
        total_calculations = len(history)

    # Prepare chart data
    if history:
        labels = [str(calc['date']).split(' ')[0] for calc in history if calc['date']]
        revenue_data = [float(calc['gross_income'] or 0) for calc in history]
        gst_data = [float(calc['gst_payable'] or 0) for calc in history]
        tax_data = [float(calc['final_tax_payable'] or 0) for calc in history]
    else:
        labels = []
        revenue_data = []
        gst_data = []
        tax_data = []

    return render_template('dash_bus.html', history=history, total_calculations=total_calculations, pan_number=pan_id, labels=labels, revenue_data=revenue_data, gst_data=gst_data, tax_data=tax_data)

@app.route('/dashboard/job')
def dashboard_job():
    pan_id = session.get('pan_id')
    if not pan_id:
        return redirect(url_for('signup'))

    # Check if user has completed setup
    if not session.get('user_category') or not session.get('person_id'):
        return redirect(url_for('category'))
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        history = cursor.execute('SELECT financial_year, gross_income, tax, net_income, insights, created_at as date FROM tax_results_job WHERE pan_id = ? ORDER BY created_at DESC', (pan_id,)).fetchall()
        total_calculations = len(history)

    # Prepare chart data
    if history:
        labels = [str(calc['financial_year']) for calc in history if calc['financial_year']]
        gross_income_data = [float(calc['gross_income'] or 0) for calc in history]
        tax_data = [float(calc['tax'] or 0) for calc in history]
        net_income_data = [float(calc['net_income'] or 0) for calc in history]
    else:
        labels = []
        gross_income_data = []
        tax_data = []
        net_income_data = []

    return render_template('dash_job.html', history=history, total_calculations=total_calculations, pan_number=pan_id, labels=labels, gross_income_data=gross_income_data, tax_data=tax_data, net_income_data=net_income_data)


if __name__ == '__main__':
    app.run(debug=True)

