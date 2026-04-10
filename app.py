from database import database
from routes import app
from admin_routes import *

# Initialize database on startup
database.init_db

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
