import sqlite3
from pathlib import Path
import datetime
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "medicine_reminder.db"

schema = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
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
    """,
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
    """,
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
    """,
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
    """,
]

sample_user = {
    "name": "Alex Green",
    "email": "alex@example.com",
    "password": generate_password_hash("Password123"),
    "created_at": datetime.datetime.utcnow().isoformat(),
}

sample_medicines = [
    {
        "name": "Vitamin D",
        "dosage": "1000 IU",
        "date": datetime.date.today().isoformat(),
        "time": "08:00",
        "frequency": "Daily",
        "food_relation": "After Food",
        "priority": "Normal",
        "notes": "Take with breakfast.",
        "stock": 15,
        "status": "pending",
        "created_at": datetime.datetime.utcnow().isoformat(),
    },
    {
        "name": "Omega 3",
        "dosage": "500 mg",
        "date": datetime.date.today().isoformat(),
        "time": "20:00",
        "frequency": "Daily",
        "food_relation": "After Food",
        "priority": "Normal",
        "notes": "Helps heart health.",
        "stock": 8,
        "status": "pending",
        "created_at": datetime.datetime.utcnow().isoformat(),
    },
    {
        "name": "Allergy Relief",
        "dosage": "10 mg",
        "date": (datetime.date.today() + datetime.timedelta(days=1)).isoformat(),
        "time": "09:00",
        "frequency": "Weekly",
        "food_relation": "Before Food",
        "priority": "High",
        "notes": "Take on busy commute days.",
        "stock": 5,
        "status": "pending",
        "created_at": datetime.datetime.utcnow().isoformat(),
    },
]

sample_family = [
    {"name": "Maya Green", "relation": "Sister", "age": 24, "notes": "Check her vitamin schedule."},
    {"name": "Daniel Green", "relation": "Father", "age": 52, "notes": "Keep emergency pills ready."},
]

sample_reminders = [
    {"reminder_time": f"{datetime.date.today().isoformat()}T08:00:00"},
    {"reminder_time": f"{datetime.date.today().isoformat()}T20:00:00"},
]


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for sql in schema:
        c.execute(sql)
    conn.commit()

    user_exists = c.execute("SELECT id FROM users WHERE email = ?", (sample_user["email"],)).fetchone()
    if user_exists:
        print("Sample user already exists. Database setup complete.")
        conn.close()
        return

    c.execute(
        "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
        (sample_user["name"], sample_user["email"], sample_user["password"], sample_user["created_at"]),
    )
    user_id = c.lastrowid

    for med in sample_medicines:
        c.execute(
            "INSERT INTO medicines (user_id, name, dosage, date, time, frequency, food_relation, priority, notes, stock, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                med["name"],
                med["dosage"],
                med["date"],
                med["time"],
                med["frequency"],
                med["food_relation"],
                med["priority"],
                med["notes"],
                med["stock"],
                med["status"],
                med["created_at"],
            ),
        )

    for member in sample_family:
        c.execute(
            "INSERT INTO family_members (user_id, name, relation, age, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                member["name"],
                member["relation"],
                member["age"],
                member["notes"],
                datetime.datetime.utcnow().isoformat(),
            ),
        )

    medicine_ids = [row[0] for row in c.execute("SELECT id FROM medicines WHERE user_id = ?", (user_id,)).fetchall()]
    for index, reminder in enumerate(sample_reminders):
        med_id = medicine_ids[index] if index < len(medicine_ids) else None
        c.execute(
            "INSERT INTO reminders (user_id, medicine_id, reminder_time, active, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, med_id, reminder["reminder_time"], 1, datetime.datetime.utcnow().isoformat()),
        )

    conn.commit()
    conn.close()
    print("Database created and sample data inserted.")


if __name__ == "__main__":
    setup_database()
