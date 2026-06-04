import os
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, session, g, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get('DATABASE', os.path.join(BASE_DIR, 'medicine_reminder.db'))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['DATABASE'] = DATABASE


# -------------------- Database helpers --------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid


# -------------------- Auth helpers --------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    if 'user_id' in session:
        user = query_db('SELECT * FROM users WHERE id = ?', [session['user_id']], one=True)
        return user
    return None


# -------------------- Routes --------------------
@app.route('/')
def index():
    return render_template('index.html', user=get_current_user())


# Authentication
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username') or request.form.get('name') or 'User'
        email = request.form['email'].strip()
        password = request.form['password']
        if query_db('SELECT id FROM users WHERE email = ?', [email], one=True):
            return render_template('signup.html', error='Email already registered')
        pw_hash = generate_password_hash(password)
        execute_db('INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
                   (username, email, pw_hash, datetime.utcnow()))
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE email = ?', [email], one=True)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    today_str = date.today().isoformat()
    todays = query_db('SELECT * FROM medicines WHERE user_id = ? AND date = ? ORDER BY time', (user['id'], today_str))
    total = len(todays)
    taken = len([m for m in todays if m['status'] == 'taken'])
    completion = int((taken / total * 100) if total else 0)
    upcoming = query_db('SELECT * FROM medicines WHERE user_id = ? AND date >= ? ORDER BY date, time LIMIT 10', (user['id'], today_str))
    missed = query_db('SELECT * FROM medicines WHERE user_id = ? AND date < ? AND status = "pending"', (user['id'], today_str))
    # For demo simplicity, send minimal stats
    return render_template('dashboard.html', user=user, todays=todays, completion=completion, upcoming=upcoming, missed=missed, tips=[], labels=[], progress_data=[], streak=0)


# Medicines CRUD
@app.route('/medicines')
@login_required
def medicines():
    user = get_current_user()
    q = request.args.get('q', '')
    freq = request.args.get('frequency', '')
    sql = 'SELECT * FROM medicines WHERE user_id = ?'
    params = [user['id']]
    if q:
        sql += ' AND (medicine_name LIKE ? OR notes LIKE ?)'
        params.extend([f'%{q}%', f'%{q}%'])
    if freq:
        sql += ' AND frequency = ?'
        params.append(freq)
    sql += ' ORDER BY date, time'
    meds = query_db(sql, params)
    return render_template('medicines.html', user=user, medicines=meds, q=q, freq=freq)


@app.route('/medicines/add', methods=['GET', 'POST'])
@login_required
def add_medicine():
    user = get_current_user()
    if request.method == 'POST':
        data = {
            'medicine_name': request.form.get('medicine_name'),
            'dosage': request.form.get('dosage'),
            'date': request.form.get('date'),
            'time': request.form.get('time'),
            'frequency': request.form.get('frequency'),
            'before_after': request.form.get('before_after'),
            'priority': request.form.get('priority'),
            'notes': request.form.get('notes'),
            'user_id': user['id']
        }
        execute_db('''INSERT INTO medicines (user_id, medicine_name, dosage, date, time, frequency, before_after, priority, notes, status, created_at)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)''',
                   (data['user_id'], data['medicine_name'], data['dosage'], data['date'], data['time'], data['frequency'], data['before_after'], data['priority'], data['notes'], datetime.utcnow()))
        return redirect(url_for('medicines'))
    return render_template('add_edit_medicine.html', user=user, edit=False)


@app.route('/medicines/edit/<int:mid>', methods=['GET', 'POST'])
@login_required
def edit_medicine(mid):
    user = get_current_user()
    med = query_db('SELECT * FROM medicines WHERE id = ? AND user_id = ?', (mid, user['id']), one=True)
    if not med:
        return redirect(url_for('medicines'))
    if request.method == 'POST':
        execute_db('''UPDATE medicines SET medicine_name=?, dosage=?, date=?, time=?, frequency=?, before_after=?, priority=?, notes=? WHERE id=?''',
                   (request.form.get('medicine_name'), request.form.get('dosage'), request.form.get('date'), request.form.get('time'), request.form.get('frequency'), request.form.get('before_after'), request.form.get('priority'), request.form.get('notes'), mid))
        return redirect(url_for('medicines'))
    return render_template('add_edit_medicine.html', user=user, med=med, edit=True)


@app.route('/medicines/delete/<int:mid>', methods=['POST'])
@login_required
def delete_medicine(mid):
    user = get_current_user()
    execute_db('DELETE FROM medicines WHERE id = ? AND user_id = ?', (mid, user['id']))
    return redirect(url_for('medicines'))


@app.route('/medicines/mark/<int:mid>/<string:action>', methods=['POST'])
@login_required
def mark_medicine(mid, action):
    user = get_current_user()
    if action == 'taken':
        execute_db('UPDATE medicines SET status = "taken" WHERE id = ? AND user_id = ?', (mid, user['id']))
        execute_db('INSERT INTO history (user_id, medicine_id, action, timestamp) VALUES (?, ?, ?, ?)', (user['id'], mid, 'taken', datetime.utcnow()))
    elif action == 'skipped':
        execute_db('UPDATE medicines SET status = "skipped" WHERE id = ? AND user_id = ?', (mid, user['id']))
        execute_db('INSERT INTO history (user_id, medicine_id, action, timestamp) VALUES (?, ?, ?, ?)', (user['id'], mid, 'skipped', datetime.utcnow()))
    return jsonify({'status': 'ok'})


# API: reminders for client-side polling
@app.route('/api/reminders')
@login_required
def api_reminders():
    user = get_current_user()
    today = date.today().isoformat()
    meds = query_db('SELECT id, medicine_name, date, time, frequency, before_after, priority, status FROM medicines WHERE user_id = ? AND date = ? AND status = "pending"', (user['id'], today))
    items = [dict(m) for m in meds]
    return jsonify(items)


# History and reports
@app.route('/history')
@login_required
def history():
    user = get_current_user()
    logs = query_db('SELECT h.*, m.medicine_name FROM history h LEFT JOIN medicines m ON h.medicine_id = m.id WHERE h.user_id = ? ORDER BY timestamp DESC', (user['id'],))
    return render_template('history.html', user=user, logs=logs)


@app.route('/api/history')
@login_required
def api_history():
    user = get_current_user()
    logs = query_db('SELECT h.*, m.medicine_name FROM history h LEFT JOIN medicines m ON h.medicine_id = m.id WHERE h.user_id = ? ORDER BY timestamp DESC', (user['id'],))
    return jsonify([dict(r) for r in logs])


# Simple family members
@app.route('/family', methods=['GET', 'POST'])
@login_required
def family():
    user = get_current_user()
    if request.method == 'POST':
        name = request.form.get('name')
        relation = request.form.get('relation')
        execute_db('INSERT INTO family_members (user_id, name, relation) VALUES (?, ?, ?)', (user['id'], name, relation))
        return redirect(url_for('family'))
    members = query_db('SELECT * FROM family_members WHERE user_id = ?', (user['id'],))
    return render_template('family.html', user=user, members=members)


# Static utilities
@app.route('/manifest.json')
def manifest():
    return send_file(os.path.join('static', 'manifest.json'))


# -------------------- DB Initialization Helper --------------------
def init_db():
    if not os.path.exists(os.path.join(BASE_DIR, 'init_db.sql')):
        return
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.executescript(open(os.path.join(BASE_DIR, 'init_db.sql')).read())
        db.commit()


if __name__ == '__main__':
    # If DB missing, initialize
    if not os.path.exists(DATABASE):
        if not os.path.exists(os.path.join(BASE_DIR, 'init_db.sql')):
            print('Database schema missing: init_db.sql not found. Please ensure it exists.')
        else:
            print('Initializing database...')
            init_db()
            print('Done. You can create a user at /signup')
    app.run(debug=True)
