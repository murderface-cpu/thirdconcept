import sqlite3
from werkzeug.security import generate_password_hash # type: ignore

class database():
    # Database initialization
    def init_db():
        conn = sqlite3.connect('third_concept.db')
        c = conn.cursor()

        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1)''')

        # Contact submissions table
        c.execute('''CREATE TABLE IF NOT EXISTS contact_submissions
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    organization TEXT,
                    subject TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT DEFAULT 'unread',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP)''')

        # Site settings table
        c.execute('''CREATE TABLE IF NOT EXISTS site_settings
                    (key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Analytics table
        c.execute('''CREATE TABLE IF NOT EXISTS analytics
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Projects table
        c.execute('''CREATE TABLE IF NOT EXISTS projects
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    icon TEXT DEFAULT '🌱',
                    tags TEXT,
                    status TEXT DEFAULT 'active',
                    image_path TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Team members table
        c.execute('''CREATE TABLE IF NOT EXISTS team_members
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    bio TEXT,
                    avatar TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Create default admin user if not exists
        c.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        if c.fetchone()[0] == 0:
            admin_hash = generate_password_hash('admin123')
            c.execute("INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    ('admin', 'admin@thirdconcept.co.ke', admin_hash, 'admin'))

        # Insert default site settings
        default_settings = [
            ('site_name', 'Third Concept'),
            ('site_description', 'Sustainable Innovation for Tomorrow'),
            ('contact_email', 'thirdconcept2025@gmail.com'),
            ('phone', '+254 700 000 000'),
            ('address', 'Nairobi, Kenya'),
            ('maintenance_mode', 'false')
        ]

        for key, value in default_settings:
            c.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (key, value))

        conn.commit()
        conn.close()