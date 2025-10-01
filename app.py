from flask import Flask, request, render_template, redirect, flash, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from calc_job import calc_job_tax_new_regime  
from calc_bus import calc_bus_tax_new_regime  
from calc_gst import calculate_gst 
from bus_pdf_gen import create_tax_report as create_business_report
import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
from flask import send_file
from pdf_gen import create_tax_report

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found. AI features will be disabled.")

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Absolute base dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'database/mydata.db')

# helper to safely convert
def get_float(key):
    try:
        return float(request.form.get(key, 0) or 0)
    except ValueError:
        return 0

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
    return render_template("buss_deduct.html")

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
        
        session['person_id'] = person_id 

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
            business_id = cursor.lastrowid
            session['business_id'] = business_id

        conn.commit()
        flash("Details submitted successfully!")

        if category == "Business Person":
            return redirect(url_for("business"))
        elif category == "Job Person":
            return redirect(url_for("job_det"))
        else:
            flash("Please select a valid category")
            return redirect(url_for("details"))


# In app.py, DELETE your existing 'businessdet', 'bussdeduct', 
# and 'bus_result' functions and REPLACE them with this block:

# Handles the submission from the business income/details form
@app.route('/details/Business', methods=['POST'])
def businessdet():
    # Get income and GST details from the form
    grin = get_float('gr-in')
    othin = get_float('oth-in')
    total_rev = grin + othin # Calculate total revenue here
    Bus = request.form.get('Bus')
    prname = request.form.get('pr-name')
    purprice = get_float('pur-price')
    purgst = get_float('pur-gst')
    tosp = request.form.get('tos-p')
    salprice = get_float('sal-price')
    sellgst = get_float('sell-gst')
    toss = request.form.get('tos-s')
    business_id = session.get('business_id')

    # Save data to the database (your code is correct here)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO income_details(business_id, gross_income, other_income, Total_revenue)
        VALUES(?,?,?,?)''', (business_id, grin, othin, total_rev))
        cursor.execute('''INSERT INTO business_details(business_id, business_name, product_name, purchase_value, gst_rate_purchase, type_of_supply_purchase, sell_value, gst_rate_sell, type_of_supply_sell)
        VALUES(?,?,?,?,?,?,?,?,?)''', (business_id, Bus, prname, purprice, purgst, tosp, salprice, sellgst, toss))
        conn.commit()

    # Save data to the session
    session['business_income'] = {'gross_income': grin, 'other_income': othin, 'total_income': total_rev}
    session['business_details'] = {'purchase_value': get_float('pur-price'), 'gst_rate_purchase': get_float('pur-gst'), 'type_of_supply_purchase': request.form.get('tos-p'), 'sell_value': get_float('sal-price'), 'gst_rate_sell': get_float('sell-gst'), 'type_of_supply_sell': request.form.get('tos-s')}

    flash("Business details submitted successfully!")
    return redirect(url_for("bus_deduct"))

# Handles the submission from the business expenses/deductions form
# In app.py

@app.route('/details/Business/deduct', methods=['POST'])
def bussdeduct():
    # Get expenses and finance deductions from the form
    rent = get_float('rent')
    emp_w = get_float('emp-w')
    Bus_op = get_float('op-exp')
    sub = get_float('sub')
    oth = get_float('oth-expenses')
    section80c = get_float('section-80c')
    section80d = get_float('section-80d')
    other_deduction = get_float('other-ded')

    # --- DATABASE INSERTION CODE ---
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Insert into the business_expenses table
        cursor.execute('''
            INSERT INTO business_expenses (rent, employee_wage, operating_expenses, subscription, other_expenses)
            VALUES (?, ?, ?, ?, ?)
        ''', (rent, emp_w, Bus_op, sub, oth))

        # Insert into the finance_deduction table
        cursor.execute('''
            INSERT INTO finance_deduction (section_80c, section_80d, other_deduction)
            VALUES (?, ?, ?)
        ''', (section80c, section80d, other_deduction))
        
        conn.commit()
    # --------------------------------

    # Save data to the session (with the typo fixed)
    session['business_expenses'] = {
        'rent': rent,
        'employee_wage': emp_w,
        'operating_expenses': Bus_op, # Corrected from 'op-exp'
        'subscription': sub,
        'other_expenses': oth
    }
    session['finance_deduction'] = {
        'section_80c': section80c,
        'section_80d': section80d,
        'other_deduction': other_deduction
    }
    
    flash("Expenses and deductions submitted successfully!")
    # Redirect to the result page
    return redirect(url_for("bus_result"))

# In app.py, replace your bus_result function with this one:

@app.route('/details/Business/result')
def bus_result():
    # 1. Check if all required session data exists
    required_keys = ['business_income', 'business_details', 'business_expenses', 'finance_deduction']
    if not all(key in session for key in required_keys):
        flash("Session data is missing. Please fill out the business forms again.")
        return redirect(url_for('business'))

    # 2. Get the correct data from the session
    bus_income = session.get('business_income', {})
    bus_details = session.get('business_details', {})
    bus_expenses = session.get('business_expenses', {})
    fin_deductions = session.get('finance_deduction', {})
    
    # --- ITR & GST Calculations (no change) ---
    gross_revenue = bus_income.get('total_income', 0)
    total_expenses = sum(bus_expenses.values())
    final_tax_payable, net_taxable_income = calc_bus_tax_new_regime(gross_revenue, total_expenses)

    gst_results = calculate_gst(
        bus_details.get('purchase_value', 0), int(bus_details.get('gst_rate_purchase', 0)),
        bus_details.get('type_of_supply_purchase', ''), bus_details.get('sell_value', 0),
        int(bus_details.get('gst_rate_sell', 0)), bus_details.get('type_of_supply_sell', '')
    )
    final_gst_payable = gst_results['net_payable']['total']

    # --- NEW: Call Gemini for Business Insights ---
    insights = ""
    if GEMINI_API_KEY:
        try:
            # 1. Create a prompt tailored for a business owner
            prompt = f"""
            You are a helpful Indian tax-saving assistant. Analyze the following data for a business owner and provide 2-3 simple, actionable tax-saving tips in bullet points.

            **User's Financial Data:**
            - Total Annual Revenue: ₹{gross_revenue:,.2f}
            - Total Business Expenses: ₹{total_expenses:,.2f}
            - Section 80C Investment: ₹{fin_deductions.get('section_80c', 0):,.2f}
            - Section 80D (Health Insurance): ₹{fin_deductions.get('section_80d', 0):,.2f}

            **Your Task:**
            Based on the data above, provide 2-3 personalized and easy-to-understand tips in bullet points on how this user could potentially save more on income tax next year.
            Focus on areas where their deductions seem low or where common tax-saving opportunities might exist for a business owner (like presumptive tax, cash expenses, etc.).
            """

            # 2. Call the Gemini API
            model = genai.GenerativeModel('gemini-pro-latest')
            response = model.generate_content(prompt)
            insights = response.text

        except Exception as e:
            print(f"Error calling Gemini API for business report: {e}")
            insights = "Could not generate AI insights at this time."

    # --- Save results to database ---
    person_id = session.get('person_id')
    business_id = session.get('business_id')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tax_results_business (person_id, business_id, gross_income, net_taxable_income, gst_payable, final_tax_payable, insights)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (person_id, business_id, round(gross_revenue, 2), round(net_taxable_income, 2), round(final_gst_payable, 2), round(final_tax_payable, 2), insights))
        conn.commit()

    # 3. Render the template with all the final values
    return render_template(
        "tax_result_bus.html",
        gross_income=round(gross_revenue, 2),
        net_taxable_income=round(net_taxable_income, 2),
        gst_payable=round(final_gst_payable, 2),
        final_tax_payable=round(final_tax_payable, 2),
        insights=insights
    )
# JOB DETAILS
@app.route('/details/Job', methods=['POST'])
def jobdet():
    fin_y = request.form.get('financial_year')
    bas_sal = get_float('basic_salary')
    hra_rec = get_float('hra_received')
    sav_int = get_float('savings_interest')
    fd_int = get_float('fd_interest')
    oth_inc = get_float('other_income')

    # ✅ Save in DB
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO job_details(financial_year, basic_salary, hra_received, interest_savings, interest_fd, other_income)
            VALUES(?,?,?,?,?,?)
        ''', (fin_y, bas_sal, hra_rec, sav_int, fd_int, oth_inc))
        conn.commit()

    # ✅ Also save in session
    session['job_income'] = {
        'financial_year': fin_y,
        'basic_salary': bas_sal,
        'hra_received': hra_rec,
        'savings_interest': sav_int,
        'fd_interest': fd_int,
        'other_income': oth_inc
    }

    flash("Job details submitted successfully!")
    return redirect(url_for("job_deduct"))




# JOB DEDUCTIONS
@app.route('/details/Job/deduct', methods=['POST'])
def jobdeduct():
    epf_ppf = get_float('epf_ppf')
    life_ins = get_float('life_insurance')
    elss = get_float('elss')
    home_loan_principal = get_float('home_loan_principal')
    tuition = get_float('tuition_fees')
    other_80c = get_float('other_80c')
    health_ins_self = get_float('health_insurance_self')
    health_ins_parents = get_float('health_insurance_parents')
    home_loan_interest = get_float('home_loan_interest')
    education_loan = get_float('education_loan_interest')
    donations = get_float('donations')
    tds = get_float('tds')

    # ✅ Save in DB
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO job_deductions(
                section_80c_epf_ppf, section_80c_life_insurance, section_80c_elss_mutual_funds,
                section_80c_home_loan_principal, section_80c_childrens_tuition, section_80c_other_investments,
                section_80d_health_insurance_self_family, section_80d_health_insurance_parents,
                section_24_home_loan_interest_paid, section_80e_education_loan_interest_paid,
                section_80g_donations_charity, tds
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (epf_ppf, life_ins, elss, home_loan_principal, tuition,
              other_80c, health_ins_self, health_ins_parents,
              home_loan_interest, education_loan, donations, tds))
        conn.commit()

    # ✅ Also save in session
    session['job_deductions'] = {
        'epf_ppf': epf_ppf,
        'life_ins': life_ins,
        'elss': elss,
        'home_loan_principal': home_loan_principal,
        'tuition': tuition,
        'other_80c': other_80c,
        'health_ins_self': health_ins_self,
        'health_ins_parents': health_ins_parents,
        'home_loan_interest': home_loan_interest,
        'education_loan': education_loan,
        'donations': donations,
        'tds': tds
    }

    flash("Job deductions submitted successfully!")
    return redirect(url_for("job_result"))


# In app.py

@app.route('/details/Job/result')
def job_result():
    job_income = session.get('job_income', {})
    job_deductions = session.get('job_deductions', {})

    # --- Your existing code to get income values (This is correct) ---
    bas_sal = job_income.get('basic_salary', 0)
    hra_rec = job_income.get('hra_received', 0)
    sav_int = job_income.get('savings_interest', 0)
    fd_int = job_income.get('fd_interest', 0)
    oth_inc = job_income.get('other_income', 0)
    tds = job_deductions.get('tds', 0)
    gross_income = bas_sal + hra_rec + sav_int + fd_int + oth_inc
    
    # --- Your tax calculation (This is correct) ---
    final_tax_due, taxable_income = calc_job_tax_new_regime(gross_income, tds)

    # --- CORRECTED SECTION for AI Insights ---
    insights = ""
    if GEMINI_API_KEY:
        try:
            # 1. Correctly gather and sum the deduction data for the prompt
            section_80c_total = (
                job_deductions.get('epf_ppf', 0) +
                job_deductions.get('life_ins', 0) +
                job_deductions.get('elss', 0) +
                job_deductions.get('home_loan_principal', 0) +
                job_deductions.get('tuition', 0) +
                job_deductions.get('other_80c', 0)
            )

            health_insurance_80d = (
                job_deductions.get('health_ins_self', 0) +
                job_deductions.get('health_ins_parents', 0)
            )

            # 2. Create the prompt using the new, correct variables
            prompt = f"""
            You are a helpful Indian tax-saving assistant. Analyze the following data for a salaried employee and provide 2-3 simple, actionable tax-saving tips in bullet points.

            **User's Financial Data:**
            - Gross Annual Salary: ₹{gross_income:,.2f}
            - Total Section 80C Investments: ₹{section_80c_total:,.2f}
            - Total Health Insurance (80D): ₹{health_insurance_80d:,.2f}

            **Your Task:**
            Based on the data above, provide 2-3 personalized and easy-to-understand tips in bullet points on how this user could potentially save more on income tax next year.
            Focus on areas where their deductions seem low compared to the available limits.
            """

            # 3. Call the Gemini API
            model = genai.GenerativeModel('gemini-pro-latest')
            response = model.generate_content(prompt)
            insights = response.text

        except Exception as e:
            print(f"Error calling Gemini API for job report: {e}")
            insights = "Could not generate AI insights at this time."

    # --- Save results to database ---
    person_id = session.get('person_id')
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tax_results_job (person_id, tax, net_income, gross_income, insights)
            VALUES (?, ?, ?, ?, ?)
        ''', (person_id, round(final_tax_due, 2), round(taxable_income, 2), round(gross_income, 2), insights))
        conn.commit()

    # Pass all correct values to the template
    return render_template(
        "tax_result_job.html",
        tax=final_tax_due,
        net_income=taxable_income,
        gross_income=gross_income,
        insights=insights
    )

@app.route('/details/Business/deduct/result', methods=['POST'])
def business_gst_result():
    # 1. Get values from the form (no change here)
    purchase_value = float(request.form.get('pur-price', 0))
    purchase_gst_rate = int(request.form.get('pur-gst', 0))
    purchase_supply_type = request.form.get('tos-p')
    sell_value = float(request.form.get('sal-price', 0))
    sell_gst_rate = int(request.form.get('sell-gst', 0))
    sell_supply_type = request.form.get('tos-s')

    # 2. Call the full calculation function (no change here)
    gst_results = calculate_gst(
        purchase_value, 
        purchase_gst_rate, 
        purchase_supply_type, 
        sell_value, 
        sell_gst_rate, 
        sell_supply_type
    )

    # 3. Prepare the simplified variables for the summary page
    final_gst_payable = gst_results['net_payable']['total']
    taxable_value = sell_value  # For GST, the taxable value is the sell value
    net_income = sell_value - purchase_value # This is the profit/net income

    # 4. Render the new 'gst_summary.html' template with the simplified data
    return render_template(
        'gst_summary.html',
        final_gst_payable=final_gst_payable,
        taxable_value=taxable_value,
        net_income=net_income
    )

@app.route('/download-report')
def download_report():
    # Check for all required data
    if 'person_id' not in session or 'job_income' not in session or 'job_deductions' not in session:
        flash("Session expired or data not found. Please calculate your tax again.")
        return redirect(url_for('job_det'))

    # --- NEW: Fetch Personal Details from DB ---
    person_id = session.get('person_id')
    personal_details = {}
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row # This allows accessing columns by name
        user_data = cursor.execute("SELECT name, email, mobile_number FROM people_info WHERE id = ?", (person_id,)).fetchone()
        if user_data:
            personal_details = dict(user_data)
    # --------------------------------------------

    job_income = session.get('job_income', {})
    job_deductions = session.get('job_deductions', {})

    gross_income = (
        job_income.get('basic_salary', 0) +
        job_income.get('hra_received', 0) +
        job_income.get('savings_interest', 0) +
        job_income.get('fd_interest', 0) +
        job_income.get('other_income', 0)
    )
    
    taxable_income = gross_income - 50000
    final_tax_due, _ = calc_job_tax_new_regime(gross_income, job_deductions.get('tds', 0))
    
    # ... (your existing tax calculation logic for the PDF summary) ...
    base_tax = 0
    if taxable_income > 300000:
       if taxable_income > 1500000: base_tax = (taxable_income - 1500000) * 0.30 + 150000
       elif taxable_income > 1200000: base_tax = (taxable_income - 1200000) * 0.20 + 90000
       elif taxable_income > 900000: base_tax = (taxable_income - 900000) * 0.15 + 45000
       elif taxable_income > 600000: base_tax = (taxable_income - 600000) * 0.10 + 15000
       else: base_tax = (taxable_income - 300000) * 0.05
    total_tax = base_tax * 1.04


    # --- UPDATED: Add personal_details to the data dictionary ---
    data_for_pdf = {
        'personal': personal_details, # Pass the fetched personal details
        'financial_year': job_income.get('financial_year', 'N/A'),
        'income': job_income,
        'summary': {
            'gross_income': gross_income,
            'standard_deduction': 50000,
            'taxable_income': taxable_income,
            'total_tax': round(total_tax, 2),
            'tds': job_deductions.get('tds', 0),
            'final_tax_due': round(final_tax_due, 2)
        }
    }
    
    pdf_buffer = create_tax_report(data_for_pdf)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name='Tax_Report.pdf',
        mimetype='application/pdf'
    )

@app.route('/download-business-report')
def download_business_report():
    # 1. Check if all required session data exists
    required_sessions = ['person_id', 'business_income', 'business_details', 'business_expenses', 'finance_deduction']
    if not all(key in session for key in required_sessions):
        flash("Session expired or data is incomplete. Please fill out the business forms again.")
        return redirect(url_for('details'))

    # 2. Gather data from all session variables
    person_id = session.get('person_id')
    bus_income = session.get('business_income', {})
    bus_details = session.get('business_details', {})
    bus_expenses = session.get('business_expenses', {})
    fin_deductions = session.get('finance_deduction', {})

    # 3. Fetch personal details from the database
    personal_details = {}
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.row_factory = sqlite3.Row
        user_data = cursor.execute("SELECT name, email, mobile_number FROM people_info WHERE id = ?", (person_id,)).fetchone()
        if user_data:
            personal_details = dict(user_data)
    
    # 4. Calculate Taxable Income using your business tax calculator
    total_revenue = bus_income.get('total_income', 0)
    total_expenses = sum(bus_expenses.values())
    total_deductions = sum(fin_deductions.values())

    net_taxable_income = total_revenue - total_expenses - total_deductions
    if net_taxable_income < 0:
        net_taxable_income = 0

    # --- CORRECTED FUNCTION CALL (only 2 arguments) ---
    final_tax_due, _ = calc_bus_tax_new_regime(net_taxable_income, 0)
    # --------------------------------------------------

    # 5. Assemble the complete data dictionary for the PDF
    data_for_pdf = {
        'personal': personal_details,
        'income': {
            'gross_income': bus_income.get('gross_income', 0),
            'other_income': bus_income.get('other_income', 0),
            'total_revenue': total_revenue,
            'business_name': bus_details.get('business_name', 'N/A'),
            'product_name': bus_details.get('product_name', 'N/A'),
        },
        'gst': {
            'purchase_value': bus_details.get('purchase_value', 0),
            'purchase_rate': bus_details.get('gst_rate_purchase', 0),
            'purchase_supply_type': bus_details.get('type_of_supply_purchase', 'N/A'),
            'sell_value': bus_details.get('sell_value', 0),
            'sell_rate': bus_details.get('gst_rate_sell', 0),
            'sell_supply_type': bus_details.get('type_of_supply_sell', 'N/A')
        },
        'expenses': {
            'rent': bus_expenses.get('rent', 0),
            'wages': bus_expenses.get('employee_wage', 0),
            'operating_expenses': bus_expenses.get('operating_expenses', 0),
            'subscription': bus_expenses.get('subscription', 0),
            'other': bus_expenses.get('other_expenses', 0),
            # Note: We pass these to the PDF but they are not used in the tax calc
            '80c': fin_deductions.get('section_80c', 0),
            '80d': fin_deductions.get('section_80d', 0),
            'other_deductions': fin_deductions.get('other_deduction', 0)
        },
        'summary': {
            'taxable_income': net_taxable_income,
            'final_tax_due': final_tax_due
        }
    }
    
    # 6. Generate the PDF
    pdf_buffer = create_business_report(data_for_pdf)

    # 7. Send the PDF file
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name='Business_Tax_Report.pdf',
        mimetype='application/pdf'
    )

# FINAL OUTPUT
@app.route('/index')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
