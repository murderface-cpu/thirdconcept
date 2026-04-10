from flask import Flask, render_template, request, flash, redirect, url_for
import os
import sqlite3
import secrets
from datetime import datetime
from forms import *

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Helper functions
def log_page_view(page):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("INSERT INTO analytics (page, ip_address, user_agent) VALUES (?, ?, ?)",
              (page, request.remote_addr, request.headers.get('User-Agent', '')))
    conn.commit()
    conn.close()

# Public routes
@app.route('/')
def home():
    log_page_view('home')
    return render_template('index.html', current_page='home')

@app.route('/about')
def about():
    log_page_view('about')
    return render_template('index.html', current_page='about')

@app.route('/services')
def services():
    log_page_view('services')
    return render_template('index.html', current_page='services')
    
@app.route('/activities')
def activities():
    log_page_view('projects')
    # Get projects from database
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE status = 'active' ORDER BY created_at DESC")
    projects_data = c.fetchall()
    conn.close()
    return render_template('index.html', current_page='projects', projects=projects_data)
    
@app.route('/team')
def team():
    log_page_view('team')
    # Get team members from database
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT * FROM team_members WHERE is_active = 1 ORDER BY created_at")
    team_data = c.fetchall()
    conn.close()
    return render_template('index.html', current_page='team', team=team_data)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    log_page_view('contact')
    form = ContactForm()
    if form.validate_on_submit():
        # Save to database
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("""INSERT INTO contact_submissions
                     (name, email, organization, subject, message)
                     VALUES (?, ?, ?, ?, ?)""",
                  (form.name.data, form.email.data, form.organization.data,
                   form.subject.data, form.message.data))
        conn.commit()
        conn.close()

        flash('Thank you for your message! We will get back to you within 24 hours.', 'success')
        return redirect(url_for('contact'))
    return render_template('index.html', current_page='contact', form=form)

@app.route('/projects/<identifier>')
def project_detail(identifier):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()

    c.execute("""
        SELECT * FROM projects WHERE 
            id = ? OR 
            LOWER(REPLACE(title, ' ', '-')) = ?
        """, (identifier, identifier))
    
    project = c.fetchone()
    conn.close()

    if not project:
        flash("Failed to open project details.", "fail")
        os.abort()

    return render_template(
        'index.html', 
        current_page='project_detail',
        project=project,
        current_year=datetime.now().year
    )

