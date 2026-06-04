-- SQLite schema for Medicine Reminder App

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at DATETIME
);

CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    dosage TEXT,
    date TEXT,
    time TEXT,
    frequency TEXT,
    before_after TEXT,
    priority TEXT,
    notes TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    medicine_id INTEGER,
    action TEXT,
    timestamp DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(medicine_id) REFERENCES medicines(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    medicine_id INTEGER,
    remind_at DATETIME,
    created_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(medicine_id) REFERENCES medicines(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT,
    relation TEXT,
    created_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Sample seed data (one demo user)
INSERT OR IGNORE INTO users (id, username, email, password_hash, created_at) VALUES (1, 'demo', 'demo@local', 'pbkdf2:sha256:150000$demo$6e2b8a0f4d6e2b6f5c8a9c0d8e7f4a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6', datetime('now'));

INSERT OR IGNORE INTO medicines (user_id, medicine_name, dosage, date, time, frequency, before_after, priority, notes, status, created_at) VALUES
    (1, 'Vitamin C', '500 mg', date('now'), '09:00', 'Daily', 'After Food', 'Low', 'Immune support', 'pending', datetime('now')),
    (1, 'Blood Pressure', '5 mg', date('now'), '08:00', 'Daily', 'Before Food', 'High', 'Take in morning', 'pending', datetime('now')),
    (1, 'Aspirin', '81 mg', date('now'), '10:00', 'Daily', 'Before Food', 'Medium', 'Heart health', 'pending', datetime('now'));

INSERT OR IGNORE INTO family_members (user_id, name, relation, created_at) VALUES (1, 'Alice', 'Wife', datetime('now')),
                                                              (1, 'Bob', 'Brother', datetime('now'));

INSERT OR IGNORE INTO history (user_id, medicine_id, action, timestamp) VALUES
    (1, 1, 'taken', datetime('now')),
    (1, 2, 'skipped', datetime('now'));