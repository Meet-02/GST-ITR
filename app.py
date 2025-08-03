from flask import Flask, request, render_template, redirect, flash, url_for
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
db_path = os.path.join(os.path.dirname(__file__), 'database/mydata.db')

@app.route('/')
def landing():
    return render_template('landingpage.html')

@app.route('/signup')
def sign_up():
    return render_template('sign-up.html')

def PANno(PAN):
    a = r'^[A-Z]{2}SPK[0-9]{4}[A-Z]{1}$'
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
            cursor.execute('INSERT INTO user (PAN_ID, Password) VALUES (?, ?)', (pan, password))
            conn.commit()
            flash("Signup successful")
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash("PAN number already exists")
            return render_template('sign-up.html') 

@app.route('/login', methods=['POST'])
def login():
    pan = request.form.get('PAN')
    password = request.form.get('pass')

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE PAN_ID = ? AND Password = ?', (pan, password))
        user = cursor.fetchone()
        if user:
            flash("Login successful")
            return redirect(url_for('index'))
        else:
            flash("Invalid PAN number or password")
            return render_template('sign-up.html') 

@app.route('/index')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
