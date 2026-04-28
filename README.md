# Decore Developers – POP Work Management System

A full-stack Django web application for managing POP (Plaster of Paris) work operations across multiple sites in Kerala.

## Features
- 🔐 Role-based authentication (Admin, Accountant, Main Worker, Helper, Driver)
- 👷 Employee management (Add/Edit/Deactivate)
- 🏗️ Work site management with employee assignment
- 📅 Daily attendance tracking (Present / Half Day / Absent)
- 💰 Automatic salary calculation from attendance
- 💳 Payment recording and tracking
- 📊 Dashboard with charts (Chart.js)
- 📋 Reports: Attendance, Salary, Site Labor Cost, Payments

## Tech Stack
- **Backend**: Django 4.2 (Python)
- **Frontend**: Bootstrap 5.3 + Bootstrap Icons
- **Database**: PostgreSQL (SQLite for dev)
- **Charts**: Chart.js 4.4

## Quick Start

### 1. Clone / unzip the project
```bash
cd decore_developers
```

### 2. Create & activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure database
**Option A – PostgreSQL (production)**
```bash
# Create DB and user in psql
CREATE DATABASE decore_db;
CREATE USER decore_user WITH PASSWORD 'decore_pass';
GRANT ALL PRIVILEGES ON DATABASE decore_db TO decore_user;
```
Then set env variables or edit `decore_developers/settings.py`.

**Option B – SQLite (quick local dev)**
In `decore_developers/settings.py`, comment out the PostgreSQL block and uncomment:
```python
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
```

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create superuser (Admin)
```bash
python manage.py createsuperuser
```

### 7. Run development server
```bash
python manage.py runserver
```
Visit: http://127.0.0.1:8000/

## User Roles & Permissions

| Role         | Dashboard | Employees | Sites | Attendance | Salary | Payments | Reports |
|-------------|-----------|-----------|-------|------------|--------|----------|---------|
| Admin        | ✅ Full   | ✅ CRUD  | ✅ CRUD | ✅ Full  | ✅ Full | ✅ Full | ✅ Full |
| Accountant   | ✅        | 👁 View  | 👁 View | 👁 View  | ✅ Full | ✅ Full | ✅ Full |
| Main Worker  | ✅        | 👁 Self  | 👁 Assigned | 👁 Own | — | — | — |
| Helper       | ✅        | 👁 Self  | 👁 Assigned | 👁 Own | — | — | — |
| Driver       | ✅        | 👁 Self  | — | 👁 Own | — | — | — |

## Salary Calculation Formula
```
Effective Days = Present Days + (Half Day Count × 0.5)
Gross Salary   = Effective Days × Daily Wage
Net Payable    = Gross Salary − Deductions
```

## Project Structure
```
decore_developers/
├── decore_developers/    # Project config (settings, urls, wsgi)
├── core/                 # Auth, CustomUser, dashboard
├── employees/            # Employee CRUD
├── sites_mgmt/           # Work sites & assignments
├── attendance/           # Attendance marking & history
├── salary/               # Salary generation & management
├── payments/             # Payment recording & tracking
├── reports/              # Reports & analytics
├── templates/            # All HTML templates
├── static/               # CSS, JS, images
├── requirements.txt
└── manage.py
```

## Default Admin Login
After running `createsuperuser`, log in at `/login/` with your chosen credentials.
The Django admin panel is at `/admin/`.

## Support
Built for Decore Developers, Kerala. For issues or customisation contact your developer.
