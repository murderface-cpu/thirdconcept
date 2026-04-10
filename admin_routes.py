from flask import render_template, request, jsonify, flash, redirect, url_for, session # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
from functools import wraps
import os
import sqlite3
import json
from datetime import datetime, timedelta
import secrets
from forms import *
from routes import app

# Authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))

        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        conn.close()

        if not user or user[0] != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('admin_login'))

        return f(*args, **kwargs)
    return decorated_function

def get_site_settings():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT key, value FROM site_settings")
    settings = dict(c.fetchall())
    conn.close()
    return settings

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("SELECT id, password_hash, role FROM users WHERE username = ? AND is_active = 1",
                  (form.username.data,))
        user = c.fetchone()

        if user and check_password_hash(user[1], form.password.data):
            session['user_id'] = user[0]
            session['role'] = user[2]

            # Update last login
            c.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user[0],))
            conn.commit()
            conn.close()

            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials.', 'error')

        conn.close()

    return render_template('admin_login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()

    # Get dashboard stats
    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
    new_messages = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM contact_submissions")
    total_messages = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    total_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM analytics WHERE created_at > datetime('now', '-7 days')")
    weekly_views = c.fetchone()[0]

    # Recent activity
    c.execute("""SELECT name, email, subject, created_at
                 FROM contact_submissions
                 ORDER BY created_at DESC LIMIT 5""")
    recent_messages = c.fetchall()

    # Page views by day (last 7 days)
    c.execute("""SELECT DATE(created_at) as date, COUNT(*) as views
                 FROM analytics
                 WHERE created_at > datetime('now', '-7 days')
                 GROUP BY DATE(created_at)
                 ORDER BY date""")
    daily_views = c.fetchall()

    conn.close()

    return render_template('admin_dashboard.html',
                         new_messages=new_messages,
                         total_messages=total_messages,
                         total_users=total_users,
                         weekly_views=weekly_views,
                         recent_messages=recent_messages,
                         daily_views=daily_views)

@app.route('/admin/messages')
@admin_required
def admin_messages():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("""SELECT id, name, email, organization, subject, message, status, created_at
                 FROM contact_submissions ORDER BY created_at DESC""")
    messages = c.fetchall()

    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
    new_messages = c.fetchone()[0]
    conn.close()

    return render_template('admin_messages.html', new_messages=new_messages, messages=messages)

@app.route('/admin/messages/<int:message_id>/status', methods=['POST'])
@admin_required
def update_message_status():
    data = request.get_json()
    message_id = data.get('message_id')
    status = data.get('status')

    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()

    if status == 'responded':
        c.execute("UPDATE contact_submissions SET status = ?, responded_at = CURRENT_TIMESTAMP WHERE id = ?",
                  (status, message_id))
    else:
        c.execute("UPDATE contact_submissions SET status = ? WHERE id = ?", (status, message_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, role, created_at, last_login, is_active FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
    new_messages = c.fetchone()[0]
    conn.close()

    return render_template('admin_users.html', new_messages=new_messages, users=users)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@admin_required
def admin_user_new():
    form = UserForm()
    if form.validate_on_submit():
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()

        password_hash = generate_password_hash(form.password.data) if form.password.data else ''

        try:
            c.execute("""INSERT INTO users (username, email, password_hash, role, is_active)
                         VALUES (?, ?, ?, ?, ?)""",
                      (form.username.data, form.email.data, password_hash,
                       form.role.data, form.is_active.data))
            conn.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
        finally:
            conn.close()

    return render_template('admin_user_form.html', form=form, title='New User')

@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_user_edit(user_id):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()

    if not user:
        flash("Team user not found.", "danger")
        return redirect(url_for('admin_team'))

    form = UserForm()

    if request.method == 'GET':
        form.username.data = user[1]
        form.email.data = user[2]
        form.password.data = user[3]
        form.role.data = user[4]
        form.is_active.data = bool(user[5])

    if form.validate_on_submit():
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("""
            UPDATE users
            SET username = ?, email = ?, password_hash = ?, role = ?, is_active = ?
            WHERE id = ?
        """, (
            form.username.data,
            form.email.data,
            generate_password_hash(form.password.data) if form.password.data else '',
            form.role.data,
            1 if form.is_active.data else 0,
            user_id
        ))
        conn.commit()
        conn.close()
        flash('User member updated successfully.', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_user_form.html', form=form, title='Edit User Member')
    
@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_user_delete(user_id):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User member deleted.", "success")
    return redirect(url_for('admin_users'))


# Projects
@app.route('/admin/projects')
@admin_required
def admin_projects():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT * FROM projects ORDER BY created_at DESC")
    projects = c.fetchall()
    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
    new_messages = c.fetchone()[0]
    conn.close()

    return render_template('admin_projects.html', new_messages=new_messages, projects=projects)

@app.route('/admin/projects/new', methods=['GET', 'POST'])
@admin_required
def admin_project_new():
    form = ProjectForm()
    if form.validate_on_submit():
        image_path = None

        # Handle image upload
        if form.image.data:
            image_file = form.image.data
            image_path = f"uploads/{image_file.filename}"
            image_file.save(os.path.join(app.static_folder, image_path))

        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO projects (title, description, icon, tags, status, image_path, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            form.title.data, form.description.data, form.icon.data,
            form.tags.data, form.status.data,
            image_path, form.content.data,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        conn.close()

        flash('Project created successfully!', 'success')
        return redirect(url_for('admin_projects'))

    return render_template('admin_project_form.html', form=form, title='New Project')

# Helper function to insert a project into the database
def insert_project(item):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO projects (title, description, icon, tags, status, image_path, content, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item.get('title'),
        item.get('description'),
        item.get('icon'),
        item.get('tags'),
        item.get('status'),
        item.get('image_path'),
        item.get('content'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    conn.commit()
    conn.close()

# JSON import route
@app.route('/admin/projects/import', methods=['GET', 'POST'])
def admin_project_import():
    if request.method == 'POST':
        if 'json_file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(request.url)

        file = request.files['json_file']

        if file.filename == '':
            flash('No selected file.', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith('.json'):
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    flash('Invalid JSON format. Expected a list of projects.', 'danger')
                    return redirect(request.url)

                for item in data:
                    insert_project(item)

                flash(f"{len(data)} projects imported successfully.", 'success')
                return redirect(url_for('admin_projects'))

            except Exception as e:
                flash(f'Error importing projects: {str(e)}', 'danger')
                return redirect(request.url)

        else:
            flash('Invalid file format. Please upload a .json file.', 'danger')
            return redirect(request.url)

    return render_template('admin_project_import.html')

# Database helper function
def get_project_by_id(project_id):
    conn = sqlite3.connect('third_concept.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    conn.close()
    return project

def update_project(project_id, title, description, icon, tags, status, image_path, content):
    conn = sqlite3.connect('third_concept.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE projects
        SET title = ?, description = ?, icon = ?, tags = ?, status = ?, image_path = ?, content = ?
        WHERE id = ?
    """, (title, description, icon, tags, status, image_path, content, project_id))
    conn.commit()
    conn.close()

@app.route('/admin/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@admin_required
def admin_project_edit(project_id):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = c.fetchone()
    conn.close()

    if not project:
        flash("Project not found.", "danger")
        return redirect(url_for('admin_projects'))

    form = ProjectForm()

    if request.method == 'GET':
        form.title.data = project[1]
        form.description.data = project[2]
        form.icon.data = project[3]
        form.tags.data = project[4]
        form.status.data = project[5]
        form.content.data = project[8]

    if form.validate_on_submit():
        image_path = project[7]  # existing image path

        if form.image.data:
            image_file = form.image.data
            image_path = f"uploads/{image_file.filename}"
            image_file.save(os.path.join(app.static_folder, image_path))

        update_project(
            project_id,
            form.title.data,
            form.description.data,
            form.icon.data,
            form.tags.data,
            form.status.data,
            image_path,
            form.content.data
        )

        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin_projects'))

    return render_template('admin_project_form.html', form=form, title='Edit Project')
    
@app.route('/admin/projects/delete/<int:project_id>', methods=['POST'])
def admin_project_delete(project_id):
    conn = sqlite3.connect('third_concept.db')
    cursor = conn.cursor()

    # Optional: confirm project exists before deleting
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    project = cursor.fetchone()
    if not project:
        conn.close()
        flash("Project not found.", "danger")
        return redirect(url_for('admin_projects'))

    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

    flash("Project deleted successfully.", "success")
    return redirect(url_for('admin_projects'))

@app.route('/admin/team')
@admin_required
def admin_team():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT * FROM team_members ORDER BY created_at DESC")
    team_members = c.fetchall()
    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
    new_messages = c.fetchone()[0]
    conn.close()

    return render_template('admin_team.html', new_messages=new_messages, team_members=team_members)

@app.route('/admin/team/new', methods=['GET', 'POST'])
@admin_required
def admin_team_new():
    form = TeamMemberForm()
    if form.validate_on_submit():
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO team_members (name, role, bio, avatar, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            form.name.data,
            form.role.data,
            form.bio.data,
            form.avatar.data,
            1 if form.is_active.data else 0,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        conn.commit()
        conn.close()
        flash('Team member added successfully.', 'success')
        return redirect(url_for('admin_team'))
    return render_template('admin_team_form.html', form=form, title='New Team Member')
    
@app.route('/admin/team/edit/<int:member_id>', methods=['GET', 'POST'])
@admin_required
def admin_team_edit(member_id):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT * FROM team_members WHERE id = ?", (member_id,))
    member = c.fetchone()
    conn.close()

    if not member:
        flash("Team member not found.", "danger")
        return redirect(url_for('admin_team'))

    form = TeamMemberForm()

    if request.method == 'GET':
        form.name.data = member[1]
        form.role.data = member[2]
        form.bio.data = member[3]
        form.avatar.data = member[4]
        form.is_active.data = bool(member[5])

    if form.validate_on_submit():
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("""
            UPDATE team_members
            SET name = ?, role = ?, bio = ?, avatar = ?, is_active = ?
            WHERE id = ?
        """, (
            form.name.data,
            form.role.data,
            form.bio.data,
            form.avatar.data,
            1 if form.is_active.data else 0,
            member_id
        ))
        conn.commit()
        conn.close()
        flash('Team member updated successfully.', 'success')
        return redirect(url_for('admin_team'))

    return render_template('admin_team_form.html', form=form, title='Edit Team Member')
    
@app.route('/admin/team/delete/<int:member_id>', methods=['POST'])
@admin_required
def admin_team_delete(member_id):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
    flash("Team member deleted.", "success")
    return redirect(url_for('admin_team'))

@app.route('/admin/team/import', methods=['GET', 'POST'])
@admin_required
def admin_team_import():
    if request.method == 'POST':
        if 'json_file' not in request.files:
            flash('No file part in the request.', 'danger')
            return redirect(request.url)

        file = request.files['json_file']

        if file.filename == '':
            flash('No selected file.', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith('.json'):
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    flash('Invalid JSON format. Expected a list of team members.', 'danger')
                    return redirect(request.url)

                for item in data:
                    conn = sqlite3.connect('third_concept.db')
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO team_members (name, role, bio, avatar, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        item.get('name'),
                        item.get('role'),
                        item.get('bio'),
                        item.get('avatar'),
                        1 if item.get('is_active') else 0,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    conn.commit()
                    conn.close()

                flash(f"{len(data)} team members imported successfully.", 'success')
                return redirect(url_for('admin_team'))

            except Exception as e:
                flash(f'Error importing team members: {str(e)}', 'danger')
                return redirect(request.url)

        else:
            flash('Invalid file format. Please upload a .json file.', 'danger')
            return redirect(request.url)

    return render_template('admin_team_import.html')

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    form = SettingsForm()
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
    new_messages = c.fetchone()[0]
    conn.close()

    if request.method == 'GET':
        # Load current settings
        settings = get_site_settings()
        form.site_name.data = settings.get('site_name', '')
        form.site_description.data = settings.get('site_description', '')
        form.contact_email.data = settings.get('contact_email', '')
        form.phone.data = settings.get('phone', '')
        form.address.data = settings.get('address', '')
        form.maintenance_mode.data = settings.get('maintenance_mode', 'false') == 'true'

    if form.validate_on_submit():
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
        new_messages = c.fetchone()[0]

        settings_data = [
            ('site_name', form.site_name.data),
            ('site_description', form.site_description.data),
            ('contact_email', form.contact_email.data),
            ('phone', form.phone.data),
            ('address', form.address.data),
            ('maintenance_mode', 'true' if form.maintenance_mode.data else 'false')
        ]

        for key, value in settings_data:
            c.execute("INSERT OR REPLACE INTO site_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                      (key, value))

        conn.commit()
        conn.close()

        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin_settings'))

    return render_template('admin_settings.html', new_messages=new_messages, form=form)

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()

    # Page views by page
    c.execute("""SELECT page, COUNT(*) as views
                 FROM analytics
                 GROUP BY page
                 ORDER BY views DESC""")
    page_views = c.fetchall()

    # Views by day (last 30 days)
    c.execute("""SELECT DATE(created_at) as date, COUNT(*) as views
                 FROM analytics
                 WHERE created_at > datetime('now', '-30 days')
                 GROUP BY DATE(created_at)
                 ORDER BY date""")
    daily_views = c.fetchall()

    # Top referrers (if you track them)
    c.execute("""SELECT COUNT(*) as total_views,
                        COUNT(DISTINCT ip_address) as unique_visitors
                 FROM analytics""")
    stats = c.fetchone()

    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE status = 'new'")
    new_messages = c.fetchone()[0]

    conn.close()

    return render_template('admin_analytics.html',
                         page_views=page_views,
                         new_messages=new_messages,
                         daily_views=daily_views,
                         total_views=stats[0],
                         unique_visitors=stats[1])

# API endpoints for admin dashboard
@app.route('/api/admin/stats')
@admin_required
def api_admin_stats():
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()

    # Get various stats
    c.execute("SELECT COUNT(*) FROM contact_submissions WHERE created_at > datetime('now', '-1 day')")
    daily_messages = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM analytics WHERE created_at > datetime('now', '-1 day')")
    daily_views = c.fetchone()[0]

    conn.close()

    return jsonify({
        'daily_messages': daily_messages,
        'daily_views': daily_views
    })

@app.route('/admin/messages/<int:message_id>/delete', methods=['POST'])
@admin_required
def delete_message(message_id):
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("DELETE FROM contact_submissions WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/messages/<int:message_id>/read', methods=['POST'])
@admin_required
def read_message(message_id):
    status = 'read'
    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()
    c.execute("UPDATE contact_submissions SET status = ?, responded_at = CURRENT_TIMESTAMP WHERE id = ?",
                  (status, message_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/live/settings')
def api_live_settings():
    settings = get_site_settings()

    conn = sqlite3.connect('third_concept.db')
    c = conn.cursor()

    c.execute("SELECT name, role, bio, avatar FROM team_members WHERE is_active = 1")
    team = [dict(zip(['name', 'role', 'bio', 'avatar'], row)) for row in c.fetchall()]

    c.execute("SELECT title, description, icon, tags FROM projects WHERE status = 'active'")
    projects = [dict(zip(['title', 'description', 'icon', 'tags'], row)) for row in c.fetchall()]

    conn.close()

    return jsonify({
        "site_name": settings.get("site_name", "Third Concept"),
        "contact_email": settings.get("contact_email", ""),
        "phone": settings.get("phone", ""),
        "address": settings.get("address", ""),
        "team": team,
        "projects": projects
    })

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.context_processor
def inject_site_settings():
    return {'site_settings': get_site_settings()}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

