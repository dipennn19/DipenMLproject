# Medicine Reminder App

A modern full-stack medicine reminder web app built with Python Flask, SQLite, HTML, CSS, and JavaScript.

## Features
- User signup, login, and secure session management
- Add / edit / delete medicine reminders
- Dashboard with todays medicines, completion percentage, upcoming reminders, missed reminders, and streak tracking
- Weekly progress chart using Chart.js
- Browser notifications, alarm sound, and voice reminders
- Dark mode, responsive glassmorphism UI, and mobile-friendly PWA support
- Calendar medicine view, family profiles, water reminder, SOS button, and AI health tips
- Medicine stock tracker and PDF report generation
- QR code scanner for medicine details and local storage preferences

## Folder Structure

```
MedicineReminderApp/
├── app.py
├── requirements.txt
├── README.md
├── setup_db.py
├── medicine_reminder.db (created after setup)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── medicines.html
│   ├── edit_medicine.html
│   ├── calendar.html
│   ├── family.html
│   ├── report.html
│   └── 404.html
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── main.js
│   │   ├── dashboard.js
│   │   └── auth.js
│   ├── images/
│   ├── manifest.json
│   └── service-worker.js
```

## Install Dependencies

1. Open a terminal in the project folder.
2. Create a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Setup Database

Run the setup script to create the SQLite database and sample data:

```powershell
python setup_db.py
```

This creates `medicine_reminder.db` and inserts sample users, medicines, family profiles, and reminders.

## Run the Flask App

Start the server with:

```powershell
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.

## Test Notifications

1. Log in and allow browser notifications when prompted.
2. Use the dashboard or medicine page to create a reminder for the current date/time.
3. Keep the browser tab open and wait for the reminder time.
4. The app will request permission, show a popup, speak the reminder text, and play an alarm.

## Notes
- Replace `app.secret_key` with a secure random key in production.
- This project is ready for college-level demonstration and can be extended with external APIs or authentication providers.

## Deploying to Vercel (overview)

Important: Vercel's serverless environment is ephemeral — SQLite files written to disk will not persist between invocations. For production on Vercel you should use a managed database (Postgres, MySQL, or Supabase). The instructions below show how to route requests through a serverless Python function using an ASGI wrapper.

1. Install the Vercel CLI and login:

```bash
npm i -g vercel
vercel login
```

2. Ensure `vercel.json` and `api/asgi.py` are present (this project includes them). Add `asgiref` to `requirements.txt` (already done).

3. Set environment variables in the Vercel Dashboard (Project Settings) — at minimum set `SECRET_KEY` and a production `DATABASE` connection string to an external DB.

4. Deploy:

```bash
vercel --prod
```

Notes and alternatives:
- If you must use SQLite for testing, consider deploying to Render, Railway, or a VM where persistent disk is available.
- On Vercel, point your app to an external managed DB (for example, Supabase) and update `DATABASE` accordingly. Update `app.py` to read `DATABASE` from environment if needed.

