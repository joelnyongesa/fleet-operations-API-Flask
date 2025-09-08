# Fleet Operations API (Flask)

This is a RESTful API for managing fleet operations, built with Flask. It provides endpoints for managing vehicles, drivers, trips, routes, maintenance records, charging sessions, and admin authentication.

## Features
- Admin authentication (sign up, login, logout, session management)
- CRUD operations for vehicles, drivers, trips, routes, maintenance records, and charging sessions
- Secure password hashing with bcrypt
- SQLAlchemy ORM with migrations
- CORS support for frontend integration

## Project Structure
```
root/
│   requirements.txt
│   README.md
│
├── env/                  # Python virtual environment (recommended)
├── instance/
│   └── fleet-operations.db  # SQLite database (default)
└── server/
    ├── app.py            # Main Flask application
    ├── models.py         # SQLAlchemy models
    ├── seed.py           # (Optional) Seed data script
    └── migrations/       # Alembic migration scripts
```

## Getting Started

### 1. Clone the Repository
```bash
git clone <repository-url>
cd fleet-operations-api-FLASK
```

### 2. Create and Activate a Virtual Environment
It is recommended to use a virtual environment to manage dependencies.

```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory with the following variables:

```
SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=sqlite:///instance/fleet-operations.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
APP_JSON_COMPACT=False
SESSION_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SECURE=False
REMEMBER_COOKIE_SECURE=False
```

Adjust values as needed for your environment.

### 5. Run Database Migrations
```bash
cd server
flask db upgrade
cd ..
```

### 6. Run the Application
```bash
cd server
python app.py
```
The API will be available at `http://localhost:5555/` by default.

## API Endpoints
- `/signup` - Admin registration
- `/login` - Admin login
- `/logout` - Admin logout
- `/check-session` - Check admin session
- `/vehicles`, `/vehicles/<id>` - Vehicle management
- `/drivers`, `/drivers/<id>` - Driver management
- `/trips`, `/trips/<id>` - Trip management
- `/routes`, `/routes/<id>` - Route management
- `/maintenance-records`, `/maintenance-records/<id>` - Maintenance records
- `/charging-sessions`, `/charging-sessions/<id>` - Charging sessions

## Notes
- Ensure your virtual environment is activated before running commands.
- The default database is SQLite, but you can configure another database in the `.env` file.
- For development, `debug=True` is enabled in `app.py`.

## License
This project is for demonstration and educational purposes.
