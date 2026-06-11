# Clinico — Smart Appointment System

A full-stack clinic appointment management system built with Flask + PostgreSQL.

---

## Folder Structure

```
Clinico-website/
├── app.py                     ← Flask application (all routes & logic)
├── requirements.txt
├── database/
│   └── schema.sql             ← PostgreSQL schema + seed data
├── static/
│   ├── css/
│   │   ├── style.css          ← Main website styles
│   │   └── dashboard.css      ← Dashboard & component styles
│   └── js/
│       ├── script.js          ← Hero slider & team slider
│       └── dashboard.js       ← Tab system, flash messages, auto-refresh
└── templates/
    ├── base.html              ← Shared layout (navbar, footer, flash)
    ├── index.html             ← Home page (hero, departments, doctors)
    ├── about.html             ← About page
    ├── doctor.html            ← Doctor listing with filter
    ├── contact.html           ← Contact page
    ├── login.html             ← Multi-role login (Patient / Doctor / Admin)
    ├── register.html          ← Multi-role registration
    ├── patient_dashboard.html ← Patient: book, queue token, appointments
    ├── doctor_dashboard.html  ← Doctor: queue management, slots, upcoming
    ├── doctor_reports.html    ← Doctor analytics with charts
    ├── admin_dashboard.html   ← Admin: approve doctors, manage users
    ├── admin_reports.html     ← System-wide analytics with Chart.js
    └── queue.html             ← Patient live queue/token status
```

---

## Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Create PostgreSQL database
```sql
CREATE DATABASE clinico_db;
```

### 3. Run the schema
```bash
psql -U postgres -d clinico_db -f database/schema.sql
```

### 4. Set up admin password
```python
# Run in Python to generate a hash for 'admin123'
from werkzeug.security import generate_password_hash
print(generate_password_hash('admin123'))
```
Then update the Admin row in the DB:
```sql
UPDATE Admin SET password = '<hashed_value>' WHERE username = 'admin';
```

### 5. Configure DB credentials
Edit `app.py` (or use environment variables):
```python
DB_CONFIG = {
    'host':     'localhost',
    'port':     5432,
    'database': 'clinico_db',
    'user':     'postgres',
    'password': 'your_password',
}
```

### 6. Run the app
```bash
python app.py
```
Visit: http://localhost:5000

---

## Roles & Dashboards

| Role    | Login With         | Dashboard Features |
|---------|--------------------|--------------------|
| Patient | Email + Password   | Book appointments, view token, track queue |
| Doctor  | Email + Password   | Manage today's queue, time slots, reports |
| Admin   | Username + Password| Approve doctors, manage users, system reports |

---

## Database Tables

| Table       | Key Fields |
|-------------|-----------|
| Patient     | patient_id, name, email, phone, password |
| Doctor      | doctor_id, name, specialization, clinic, fees, email, password, is_approved |
| Admin       | admin_id, username, password |
| TimeSlot    | slot_id, doctor_id, slot_date, start_time, end_time, is_available |
| Appointment | appointment_id, patient_id, doctor_id, slot_id, token_no, status, appointment_date |

---

## Default Login (after setup)
- **Admin:** username: `admin`, password: `admin123`
- **Doctor:** Register via /register (awaits admin approval)
- **Patient:** Register via /register (instant access)
