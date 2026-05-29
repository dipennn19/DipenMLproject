from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import datetime
import os

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "medicine_reminder.db"

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_secret_key")

# Initialize or migrate database tables
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dosage TEXT,
            date TEXT,
            time TEXT,
            frequency TEXT,
            food_relation TEXT,
            priority TEXT,
            notes TEXT,
            stock INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medicine_id INTEGER,
            action TEXT,
            remark TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(medicine_id) REFERENCES medicines(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medicine_id INTEGER,
            reminder_time TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(medicine_id) REFERENCES medicines(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            relation TEXT,
            age INTEGER,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def current_user():
    if "user_id" not in session:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user


def login_required(route):
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return route(*args, **kwargs)
    wrapper.__name__ = route.__name__
    return wrapper


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password or password != confirm:
            flash("Please provide valid signup details and matching passwords.", "error")
            return render_template("signup.html")

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("An account with this email already exists.", "error")
            conn.close()
            return render_template("signup.html")

        hashed = generate_password_hash(password)
        conn.execute(
            "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
            (name, email, hashed, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()
        flash("Signup successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    conn = get_db_connection()
    today_str = datetime.date.today().isoformat()

    medicines = conn.execute(
        "SELECT * FROM medicines WHERE user_id = ? ORDER BY date, time",
        (user["id"],),
    ).fetchall()
    todays = [m for m in medicines if m["date"] == today_str]
    upcoming = [m for m in medicines if m["date"] >= today_str][:5]
    missed = [m for m in medicines if m["date"] < today_str and m["status"] == "pending"]

    completed = conn.execute(
        "SELECT COUNT(*) AS cnt FROM history WHERE user_id = ? AND action = 'taken' AND timestamp >= ?",
        (user["id"], f"{today_str}T00:00:00"),
    ).fetchone()["cnt"]
    total_today = len(todays)
    completion = int(completed / total_today * 100) if total_today else 0

    progress_data = []
    labels = []
    for offset in range(6, -1, -1):
        day = datetime.date.today() - datetime.timedelta(days=offset)
        label = day.strftime("%a")
        labels.append(label)
        count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM history WHERE user_id = ? AND action = 'taken' AND timestamp LIKE ?",
            (user["id"], f"{day.isoformat()}%"),
        ).fetchone()["cnt"]
        progress_data.append(count)

    streak = 0
    for offset in range(0, 7):
        day = datetime.date.today() - datetime.timedelta(days=offset)
        count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM history WHERE user_id = ? AND action = 'taken' AND timestamp LIKE ?",
            (user["id"], f"{day.isoformat()}%"),
        ).fetchone()["cnt"]
        if count > 0:
            streak += 1
        else:
            break

    tips = [
        "Stay hydrated: water helps medicines absorb better.",
        "Set routine times for daily doses to build healthy habits.",
        "Track side effects and share updates with your care team.",
    ]

    family = conn.execute(
        "SELECT * FROM family_members WHERE user_id = ? ORDER BY name",
        (user["id"],),
    ).fetchall()

    conn.close()
    return render_template(
        "dashboard.html",
        user=user,
        todays=todays,
        upcoming=upcoming,
        missed=missed,
        completion=completion,
        labels=labels,
        progress_data=progress_data,
        streak=streak,
        tips=tips,
        family=family,
    )


@app.route("/medicines", methods=["GET", "POST"])
@login_required
def medicines():
    user = current_user()
    conn = get_db_connection()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        dosage = request.form.get("dosage", "").strip()
        date = request.form.get("date", "")
        time = request.form.get("time", "")
        frequency = request.form.get("frequency", "Daily")
        food_relation = request.form.get("food_relation", "Before Food")
        priority = request.form.get("priority", "Normal")
        notes = request.form.get("notes", "").strip()
        stock = int(request.form.get("stock", 0))

        if not name or not date or not time:
            flash("Medicine name, date, and time are required.", "error")
            return redirect(url_for("medicines"))

        conn.execute(
            "INSERT INTO medicines (user_id, name, dosage, date, time, frequency, food_relation, priority, notes, stock, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], name, dosage, date, time, frequency, food_relation, priority, notes, stock, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
        flash("Medicine added to your schedule.", "success")

    meds = conn.execute(
        "SELECT * FROM medicines WHERE user_id = ? ORDER BY date, time",
        (user["id"],),
    ).fetchall()
    conn.close()
    return render_template("medicines.html", user=user, medicines=meds)


@app.route("/medicine/edit/<int:medicine_id>", methods=["GET", "POST"])
@login_required
def edit_medicine(medicine_id):
    user = current_user()
    conn = get_db_connection()
    medicine = conn.execute(
        "SELECT * FROM medicines WHERE id = ? AND user_id = ?", (medicine_id, user["id"])
    ).fetchone()

    if not medicine:
        conn.close()
        return redirect(url_for("medicines"))

    if request.method == "POST":
        name = request.form.get("name", medicine["name"]).strip()
        dosage = request.form.get("dosage", medicine["dosage"]).strip()
        date = request.form.get("date", medicine["date"])
        time = request.form.get("time", medicine["time"])
        frequency = request.form.get("frequency", medicine["frequency"])
        food_relation = request.form.get("food_relation", medicine["food_relation"])
        priority = request.form.get("priority", medicine["priority"])
        notes = request.form.get("notes", medicine["notes"]).strip()
        stock = int(request.form.get("stock", medicine["stock"]))

        conn.execute(
            "UPDATE medicines SET name = ?, dosage = ?, date = ?, time = ?, frequency = ?, food_relation = ?, priority = ?, notes = ?, stock = ? WHERE id = ? AND user_id = ?",
            (name, dosage, date, time, frequency, food_relation, priority, notes, stock, medicine_id, user["id"]),
        )
        conn.commit()
        conn.close()
        flash("Medicine details updated successfully.", "success")
        return redirect(url_for("medicines"))

    conn.close()
    return render_template("edit_medicine.html", user=user, medicine=medicine)


@app.route("/medicine/delete/<int:medicine_id>")
@login_required
def delete_medicine(medicine_id):
    user = current_user()
    conn = get_db_connection()
    conn.execute("DELETE FROM medicines WHERE id = ? AND user_id = ?", (medicine_id, user["id"]))
    conn.execute("DELETE FROM reminders WHERE medicine_id = ? AND user_id = ?", (medicine_id, user["id"]))
    conn.commit()
    conn.close()
    flash("Medicine removed from the schedule.", "success")
    return redirect(url_for("medicines"))


@app.route("/medicine/status/<int:medicine_id>/<action>", methods=["POST"])
@login_required
def medicine_status(medicine_id, action):
    user = current_user()
    conn = get_db_connection()
    now = datetime.datetime.utcnow().isoformat()
    if action not in ["taken", "skipped"]:
        conn.close()
        return redirect(url_for("dashboard"))

    conn.execute(
        "UPDATE medicines SET status = ? WHERE id = ? AND user_id = ?",
        (action, medicine_id, user["id"]),
    )
    conn.execute(
        "INSERT INTO history (user_id, medicine_id, action, remark, timestamp) VALUES (?, ?, ?, ?, ?)",
        (user["id"], medicine_id, action, f"Marked {action}", now),
    )
    conn.commit()
    conn.close()
    flash(f"Medicine marked as {action}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/calendar")
@login_required
def calendar_view():
    user = current_user()
    conn = get_db_connection()
    medicines = conn.execute(
        "SELECT * FROM medicines WHERE user_id = ? ORDER BY date, time",
        (user["id"],),
    ).fetchall()
    conn.close()
    return render_template("calendar.html", user=user, medicines=medicines)


@app.route("/family", methods=["GET", "POST"])
@login_required
def family():
    user = current_user()
    conn = get_db_connection()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        relation = request.form.get("relation", "").strip()
        age = request.form.get("age", "0")
        notes = request.form.get("notes", "").strip()

        if not name:
            flash("Family member name is required.", "error")
            return redirect(url_for("family"))

        conn.execute(
            "INSERT INTO family_members (user_id, name, relation, age, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], name, relation, int(age or 0), notes, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()
        flash("Family profile added.", "success")

    members = conn.execute(
        "SELECT * FROM family_members WHERE user_id = ? ORDER BY name",
        (user["id"],),
    ).fetchall()
    conn.close()
    return render_template("family.html", user=user, members=members)


@app.route("/report")
@login_required
def report():
    user = current_user()
    conn = get_db_connection()
    medicines = conn.execute(
        "SELECT * FROM medicines WHERE user_id = ? ORDER BY date, time",
        (user["id"],),
    ).fetchall()
    conn.close()

    buffer = io.BytesIO()
    doc = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    doc.setTitle("Medicine History Report")
    doc.setFont("Helvetica-Bold", 18)
    doc.drawString(40, height - 50, "Medicine History Report")
    doc.setFont("Helvetica", 11)
    doc.drawString(40, height - 70, f"Patient: {user['name']} ({user['email']})")
    doc.drawString(40, height - 90, f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    y = height - 130
    for med in medicines:
        doc.setFont("Helvetica-Bold", 12)
        doc.drawString(40, y, f"{med['name']} - {med['dosage']} ({med['priority']})")
        y -= 16
        doc.setFont("Helvetica", 10)
        doc.drawString(44, y, f"Date: {med['date']} | Time: {med['time']} | Frequency: {med['frequency']} | Food: {med['food_relation']}")
        y -= 14
        doc.drawString(44, y, f"Stock: {med['stock']} | Status: {med['status']} | Notes: {med['notes']}")
        y -= 24
        if y < 80:
            doc.showPage()
            y = height - 80

    doc.save()
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="medicine_history_report.pdf",
        mimetype="application/pdf",
    )


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# Ensure the SQLite database tables exist before the app starts.
init_db()

if __name__ == "__main__":
    app.run(debug=True)
