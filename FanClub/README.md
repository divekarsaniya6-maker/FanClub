# FanClub — Football Ground Booking & Community

FanClub is a Flask + SQLite full-stack college project. It includes registration/login, venue booking, duplicate-slot protection, simulated payment, bookings, teams, team membership, matches, profile editing, and an admin dashboard.

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- Internet connection for Google Fonts and remote venue photography (the app itself runs locally without those assets)

## Run on Windows
1. Extract/open the `FanClub` folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Run these commands:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, you can skip activation and run:

```powershell
py -m pip install -r requirements.txt
py app.py
```

4. Open `http://127.0.0.1:5000` in Chrome.

You can also double-click `run_windows.bat`; it installs dependencies and starts the app.

## Development admin account
- Email: `admin@fanclub.local`
- Password: `FanClub@2026`

Change this password and use a secure secret key before hosting the site publicly. The development admin account is created automatically on first run.

## Features
- Register and login with hashed passwords
- Flask session authentication
- Venue slot booking saved in SQLite
- Unique database constraint prevents two bookings for the same venue/date/slot
- Simulated payment only; no real money is taken
- View and cancel personal bookings
- Create teams, join/leave teams, view team members
- View fixtures and create/delete fixtures as admin
- Profile editing
- Admin statistics and user/booking/team/match management

## Important: local vs live website
`http://127.0.0.1:5000` is only available on your own computer. To let friends and college staff access the website from anywhere, deploy the project to a hosting service that supports Python/Flask (for example, Render or PythonAnywhere) and configure a persistent database/storage. Do not use the development admin password or the default random secret key for production. This is a college-project demo and is not configured for real payments or production-grade deployment.
