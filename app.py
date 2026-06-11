"""
Clinico - Smart Appointment System
Flask Backend with PostgreSQL
"""

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from functools import wraps
from datetime import date, datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clinico_secret_key_2025')

# ─────────────────────────────────────────────────────────────
# DATABASE CONFIG
# ─────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST',     'localhost'),
    'port':     int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME',     'clinico_db'),
    'user':     os.environ.get('DB_USER',     'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'admin123'),
}

def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn

def query(sql, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = None
        if fetchone:
            result = cur.fetchone()
        elif fetchall:
            result = cur.fetchall()
        if commit:
            conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────
# AUTH DECORATOR
# ─────────────────────────────────────────────────────────────
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('Access denied.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ─────────────────────────────────────────────────────────────
# PUBLIC PAGES
# ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    doctors = query(
        "SELECT * FROM Doctor WHERE is_approved = TRUE LIMIT 6",
        fetchall=True
    )
    return render_template('index.html', doctors=doctors)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/doctor')
def doctor_list():
    specialization = request.args.get('specialization', '')
    if specialization:
        doctors = query(
            "SELECT * FROM Doctor WHERE is_approved=TRUE AND specialization ILIKE %s ORDER BY name",
            (f'%{specialization}%',), fetchall=True
        )
    else:
        doctors = query(
            "SELECT * FROM Doctor WHERE is_approved=TRUE ORDER BY name",
            fetchall=True
        )
    return render_template('doctor.html', doctors=doctors, specialization=specialization)

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ─────────────────────────────────────────────────────────────
# AUTH: REGISTER / LOGIN / LOGOUT
# ─────────────────────────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role', 'patient')
        name  = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        phone = request.form.get('phone', '').strip()
        pwd   = generate_password_hash(request.form['password'])

        try:
            if role == 'patient':
                query(
                    "INSERT INTO Patient (name, email, phone, password) VALUES (%s,%s,%s,%s)",
                    (name, email, phone, pwd), commit=True
                )
                flash('Registration successful! Please log in.', 'success')
            elif role == 'doctor':
                spec    = request.form.get('specialization', '').strip()
                contact = request.form.get('contact_no', '').strip()
                fees    = float(request.form.get('fees', 0))
                query(
                    """INSERT INTO Doctor
                       (name,email,contact_no,specialization,consultation_fees,password)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (name, email, contact, spec, fees, pwd), commit=True
                )
                flash('Doctor registration submitted! Await admin approval.', 'info')
        except psycopg2.errors.UniqueViolation:
            flash('Email already registered.', 'danger')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role  = request.form['role']
        email = request.form['email'].strip().lower()
        pwd   = request.form['password']

        if role == 'patient':
            user = query("SELECT * FROM Patient WHERE email=%s", (email,), fetchone=True)
            if user and check_password_hash(user['password'], pwd):
                session.update({'user_id': user['patient_id'], 'role': 'patient',
                                'name': user['name'], 'email': user['email']})
                return redirect(url_for('patient_dashboard'))

        elif role == 'doctor':
            user = query("SELECT * FROM Doctor WHERE email=%s", (email,), fetchone=True)
            if user and check_password_hash(user['password'], pwd):
                if not user['is_approved']:
                    flash('Your account is pending admin approval.', 'warning')
                    return redirect(url_for('login'))
                session.update({'user_id': user['doctor_id'], 'role': 'doctor',
                                'name': user['name'], 'email': user['email']})
                return redirect(url_for('doctor_dashboard'))

        elif role == 'admin':
            user = query("SELECT * FROM Admin WHERE username=%s", (email,), fetchone=True)
            if user and check_password_hash(user['password'], pwd):
                session.update({'user_id': user['admin_id'], 'role': 'admin',
                                'name': user['username']})
                return redirect(url_for('admin_dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ─────────────────────────────────────────────────────────────
# PATIENT DASHBOARD
# ─────────────────────────────────────────────────────────────
@app.route('/patient/dashboard')
@login_required(role='patient')
def patient_dashboard():
    pid = session['user_id']
    appointments = query(
        """SELECT a.*, d.name as doctor_name, d.specialization,
                  t.slot_date, t.start_time, t.end_time
           FROM Appointment a
           JOIN Doctor d ON a.doctor_id = d.doctor_id
           JOIN TimeSlot t ON a.slot_id = t.slot_id
           WHERE a.patient_id = %s
           ORDER BY t.slot_date DESC, t.start_time DESC""",
        (pid,), fetchall=True
    )
    doctors = query(
        "SELECT * FROM Doctor WHERE is_approved=TRUE ORDER BY specialization, name",
        fetchall=True
    )
    return render_template('patient_dashboard.html',
                           appointments=appointments, doctors=doctors)

@app.route('/patient/book', methods=['POST'])
@login_required(role='patient')
def book_appointment():
    pid       = session['user_id']
    doctor_id = int(request.form['doctor_id'])
    slot_id   = int(request.form['slot_id'])
    problem   = request.form.get('problem_desc', '').strip()

    slot = query("SELECT * FROM TimeSlot WHERE slot_id=%s AND is_available=TRUE",
                 (slot_id,), fetchone=True)
    if not slot:
        flash('Selected slot is no longer available.', 'danger')
        return redirect(url_for('patient_dashboard'))

    existing = query(
        "SELECT 1 FROM Appointment WHERE patient_id=%s AND slot_id=%s AND status NOT IN ('Cancelled','No-show')",
        (pid, slot_id), fetchone=True
    )
    if existing:
        flash('You already have an appointment for this slot.', 'warning')
        return redirect(url_for('patient_dashboard'))

    token = query(
        """SELECT COALESCE(MAX(token_no), 0) + 1 AS next_token
           FROM Appointment
           WHERE doctor_id=%s AND appointment_date=%s AND status NOT IN ('Cancelled','No-show')""",
        (doctor_id, slot['slot_date']), fetchone=True
    )['next_token']

    query(
        """INSERT INTO Appointment
           (patient_id, doctor_id, slot_id, token_no, status, appointment_date, problem_desc)
           VALUES (%s,%s,%s,%s,'Confirmed',%s,%s)""",
        (pid, doctor_id, slot_id, token, slot['slot_date'], problem), commit=True
    )
    query("UPDATE TimeSlot SET is_available=FALSE WHERE slot_id=%s", (slot_id,), commit=True)

    flash(f'Appointment booked! Your token number is #{token}', 'success')
    return redirect(url_for('patient_dashboard'))

@app.route('/patient/cancel/<int:appt_id>', methods=['POST'])
@login_required(role='patient')
def cancel_appointment(appt_id):
    pid = session['user_id']
    appt = query("SELECT * FROM Appointment WHERE appointment_id=%s AND patient_id=%s",
                 (appt_id, pid), fetchone=True)
    if appt and appt['status'] in ('Scheduled', 'Confirmed'):
        query("UPDATE Appointment SET status='Cancelled' WHERE appointment_id=%s",
              (appt_id,), commit=True)
        query("UPDATE TimeSlot SET is_available=TRUE WHERE slot_id=%s",
              (appt['slot_id'],), commit=True)
        flash('Appointment cancelled.', 'success')
    else:
        flash('Cannot cancel this appointment.', 'danger')
    return redirect(url_for('patient_dashboard'))

@app.route('/patient/queue/<int:appt_id>')
@login_required(role='patient')
def patient_queue(appt_id):
    pid  = session['user_id']
    appt = query(
        """SELECT a.*, d.name as doctor_name, d.specialization,
                  t.slot_date, t.start_time, t.end_time
           FROM Appointment a
           JOIN Doctor d ON a.doctor_id = d.doctor_id
           JOIN TimeSlot t ON a.slot_id = t.slot_id
           WHERE a.appointment_id=%s AND a.patient_id=%s""",
        (appt_id, pid), fetchone=True
    )
    if not appt:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('patient_dashboard'))
    ahead = query(
        """SELECT COUNT(*) as cnt FROM Appointment
           WHERE doctor_id=%s AND appointment_date=%s
             AND token_no < %s AND status='In Queue'""",
        (appt['doctor_id'], appt['appointment_date'], appt['token_no']), fetchone=True
    )['cnt']
    return render_template('queue.html', appt=appt, ahead=ahead)

# ─────────────────────────────────────────────────────────────
# SLOTS API (AJAX)
# ─────────────────────────────────────────────────────────────
@app.route('/api/slots/<int:doctor_id>')
@login_required(role='patient')
def get_slots(doctor_id):
    today = date.today().isoformat()

    slots = query(
        """SELECT * FROM TimeSlot
           WHERE doctor_id=%s 
           AND is_available=TRUE 
           AND slot_date >= %s
           ORDER BY slot_date, start_time""",
        (doctor_id, today),
        fetchall=True
    )

    return jsonify([
        {
            **dict(s),
            "start_time": s["start_time"].strftime("%H:%M"),
            "end_time": s["end_time"].strftime("%H:%M") if s.get("end_time") else None,
            "slot_date": s["slot_date"].isoformat()
        }
        for s in (slots or [])
    ])

# ─────────────────────────────────────────────────────────────
# DOCTOR DASHBOARD
# ─────────────────────────────────────────────────────────────
@app.route('/doctor/dashboard')
@login_required(role='doctor')
def doctor_dashboard():
    did   = session['user_id']
    today = date.today()

    today_queue = query(
        """SELECT a.*, p.name as patient_name, p.phone, a.problem_desc
           FROM Appointment a
           JOIN Patient p ON a.patient_id = p.patient_id
           WHERE a.doctor_id=%s AND a.appointment_date=%s
             AND a.status NOT IN ('Cancelled','No-show')
           ORDER BY a.token_no""",
        (did, today), fetchall=True
    )
    upcoming = query(
        """SELECT a.*, p.name as patient_name, t.slot_date, t.start_time, t.end_time
           FROM Appointment a
           JOIN Patient p ON a.patient_id = p.patient_id
           JOIN TimeSlot t ON a.slot_id = t.slot_id
           WHERE a.doctor_id=%s AND t.slot_date > %s
             AND a.status NOT IN ('Cancelled','No-show')
           ORDER BY t.slot_date, t.start_time LIMIT 10""",
        (did, today), fetchall=True
    )
    my_slots = query(
        """SELECT * FROM TimeSlot WHERE doctor_id=%s AND slot_date >= %s
           ORDER BY slot_date, start_time""",
        (did, today), fetchall=True
    )
    stats = query(
        """SELECT
             COUNT(*) FILTER (WHERE status='Completed')  AS completed,
             COUNT(*) FILTER (WHERE appointment_date=%s) AS today_total,
             COUNT(*) FILTER (WHERE status='Cancelled')  AS cancelled
           FROM Appointment WHERE doctor_id=%s""",
        (today, did), fetchone=True
    )
    return render_template('doctor_dashboard.html',
                           today_queue=today_queue, upcoming=upcoming,
                           my_slots=my_slots, stats=stats, today=today)

@app.route('/doctor/update_status/<int:appt_id>', methods=['POST'])
@login_required(role='doctor')
def update_appt_status(appt_id):
    did    = session['user_id']
    status = request.form['status']
    query(
        "UPDATE Appointment SET status=%s WHERE appointment_id=%s AND doctor_id=%s",
        (status, appt_id, did), commit=True
    )
    flash(f'Status updated to {status}.', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/add_slot', methods=['POST'])
@login_required(role='doctor')
def add_slot():
    did        = session['user_id']
    slot_date  = request.form['slot_date']
    start_time = request.form['start_time']
    end_time   = request.form['end_time']
    query(
        "INSERT INTO TimeSlot (doctor_id, slot_date, start_time, end_time) VALUES (%s,%s,%s,%s)",
        (did, slot_date, start_time, end_time), commit=True
    )
    flash('Time slot added.', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/delete_slot/<int:slot_id>', methods=['POST'])
@login_required(role='doctor')
def delete_slot(slot_id):
    did = session['user_id']
    query("DELETE FROM TimeSlot WHERE slot_id=%s AND doctor_id=%s", (slot_id, did), commit=True)
    flash('Slot deleted.', 'success')
    return redirect(url_for('doctor_dashboard'))

@app.route('/doctor/reports')
@login_required(role='doctor')
def doctor_reports():
    did = session['user_id']
    daily = query(
        """SELECT appointment_date,
                  COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE status='Completed')  AS completed,
                  COUNT(*) FILTER (WHERE status='Cancelled')  AS cancelled,
                  COUNT(*) FILTER (WHERE status='No-show')    AS no_show
           FROM Appointment WHERE doctor_id=%s
           GROUP BY appointment_date ORDER BY appointment_date DESC LIMIT 30""",
        (did,), fetchall=True
    )
    by_status = query(
        """SELECT status, COUNT(*) AS cnt
           FROM Appointment WHERE doctor_id=%s GROUP BY status""",
        (did,), fetchall=True
    )
    return render_template('doctor_reports.html', daily=daily, by_status=by_status)

# ─────────────────────────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────
@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    stats = query(
        """SELECT
            (SELECT COUNT(*) FROM Patient)                       AS total_patients,
            (SELECT COUNT(*) FROM Doctor WHERE is_approved=TRUE) AS total_doctors,
            (SELECT COUNT(*) FROM Appointment)                   AS total_appts,
            (SELECT COUNT(*) FROM Appointment WHERE status='Completed') AS completed,
            (SELECT COUNT(*) FROM Doctor WHERE is_approved=FALSE) AS pending_doctors
        """, fetchone=True
    )
    pending_doctors = query(
        "SELECT * FROM Doctor WHERE is_approved=FALSE ORDER BY created_at DESC",
        fetchall=True
    )
    recent_appts = query(
        """SELECT a.*, p.name as patient_name, d.name as doctor_name,
                  t.slot_date, t.start_time
           FROM Appointment a
           JOIN Patient p ON a.patient_id = p.patient_id
           JOIN Doctor d ON a.doctor_id = d.doctor_id
           JOIN TimeSlot t ON a.slot_id = t.slot_id
           ORDER BY a.created_at DESC LIMIT 15""",
        fetchall=True
    )
    all_patients = query(
        "SELECT * FROM Patient ORDER BY created_at DESC LIMIT 20", fetchall=True
    )
    all_doctors = query(
        "SELECT * FROM Doctor ORDER BY created_at DESC", fetchall=True
    )
    return render_template('admin_dashboard.html',
                           stats=stats, pending_doctors=pending_doctors,
                           recent_appts=recent_appts, all_patients=all_patients,
                           all_doctors=all_doctors)

@app.route('/admin/approve_doctor/<int:did>', methods=['POST'])
@login_required(role='admin')
def approve_doctor(did):
    query("UPDATE Doctor SET is_approved=TRUE WHERE doctor_id=%s", (did,), commit=True)
    flash('Doctor approved.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_doctor/<int:did>', methods=['POST'])
@login_required(role='admin')
def reject_doctor(did):
    query("DELETE FROM Doctor WHERE doctor_id=%s AND is_approved=FALSE", (did,), commit=True)
    flash('Doctor registration rejected and removed.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_patient/<int:pid>', methods=['POST'])
@login_required(role='admin')
def delete_patient(pid):
    query("DELETE FROM Patient WHERE patient_id=%s", (pid,), commit=True)
    flash('Patient removed.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reports')
@login_required(role='admin')
def admin_reports():
    daily = query(
        """SELECT appointment_date,
                  COUNT(*) AS total,
                  COUNT(*) FILTER (WHERE status='Completed') AS completed,
                  COUNT(*) FILTER (WHERE status='Cancelled') AS cancelled
           FROM Appointment
           GROUP BY appointment_date
           ORDER BY appointment_date DESC LIMIT 30""",
        fetchall=True
    )
    by_doctor = query(
        """SELECT d.name, d.specialization,
                  COUNT(a.appointment_id) AS total,
                  COUNT(a.appointment_id) FILTER (WHERE a.status='Completed') AS completed
           FROM Doctor d
           LEFT JOIN Appointment a ON d.doctor_id = a.doctor_id
           WHERE d.is_approved=TRUE
           GROUP BY d.doctor_id, d.name, d.specialization
           ORDER BY total DESC""",
        fetchall=True
    )
    by_status = query(
        "SELECT status, COUNT(*) AS cnt FROM Appointment GROUP BY status",
        fetchall=True
    )
    busy_hours = query(
        """SELECT EXTRACT(HOUR FROM t.start_time) AS hour,
                  COUNT(*) AS appts
           FROM Appointment a
           JOIN TimeSlot t ON a.slot_id = t.slot_id
           GROUP BY hour ORDER BY appts DESC LIMIT 10""",
        fetchall=True
    )
    return render_template('admin_reports.html',
                           daily=daily, by_doctor=by_doctor,
                           by_status=by_status, busy_hours=busy_hours)

# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
