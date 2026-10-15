# ⚽ FanClub – Complete Real Working Football Ground Booking Website

> **YOUR GAME. YOUR CLUB.**  
> *PLAY. BOOK. ENJOY.*

FanClub is a production-grade, full-stack football ground reservation and community platform engineered for players, squad captains, and turf facility administrators. Built with **Python Flask**, **SQLAlchemy** (supporting SQLite locally and PostgreSQL in production), **HTML5**, **CSS3**, and modern vanilla **JavaScript**, FanClub eliminates demo shortcuts, fake simulations, and hardcoded authentication in favor of a 100% database-backed architecture.

---

## 🌟 Key Functional Highlights

1. **Real User Registration & Authentication**:
   - Server-side validation of full name, email, phone number, and password (minimum 8 characters).
   - Duplicate email rejection enforced at both the application level and database unique index level.
   - Passwords cryptographically hashed using `werkzeug.security` (`scrypt` / `pbkdf2:sha256`) — never stored in plaintext.
   - Secure server-side sessions with HTTP-only and SameSite cookie protection.
   - Dedicated player profile management with password change and contact updating.

2. **Real Football Ground Bookings & Double-Booking Prevention**:
   - Featured ground: **Ryan Vibgyor KPC Empyrean** (Kharghar, Navi Mumbai) and other premier venues.
   - Dynamic real-time slot availability queries synchronized with Indian Standard Time (`Asia/Kolkata`).
   - Transactional server-side double-booking protection ensuring two users can never reserve the same venue, date, and time slot.
   - Confirmation is only issued after the booking is committed to the database.
   - Generates digital admission voucher passes with unique codes (`FC-2026-XXXX`).
   - Transparent desk settlement ("Pay at Turf Reception") and 1-click slot cancellation that instantly re-opens the slot.

3. **Secure Administrative Console**:
   - Strictly protected administrator routes enforced by the `admin_required` server decorator.
   - Real database analytics: active players, football venues, confirmed bookings, and total turnover.
   - Ground venue lifecycle management: add new grounds, update pricing/facilities, and activate/deactivate pitches.
   - Global booking ledger with live status management (`Confirmed`, `Completed`, `Cancelled`).
   - User account inspection and role assignment (promoting players or demoting admins).
   - Secure admin provisioning via CLI (`python scripts/create_admin.py`) or environment variables (`ADMIN_EMAIL` / `ADMIN_PASSWORD`). No public registration grants admin privileges.

4. **Squad & Fixture Ecosystem**:
   - Squad creation with unique alphanumeric team join codes (`FC-TEAM-XXXX`).
   - Player joining/leaving and captain roster management.
   - Friendly match scheduling between registered squads with venue locking and past-date validation.

---

## 📁 Project Directory Structure

```text
FanClub_Complete_Project/
│
├── app.py                     # Main Flask Application Server & API Endpoints
├── models.py                  # SQLAlchemy Database Models (Users, Venues, Bookings, Teams, Matches)
├── test_fanclub.py            # Automated Unit & Integration Test Suite (13 Test Cases)
├── requirements.txt           # Python Package Dependencies
├── README.md                  # Comprehensive Documentation & Setup Guide
├── .env.example               # Environment Variables Template
├── .gitignore                 # Version Control Ignore Rules
├── Procfile                   # Cloud Web Process Definition (Gunicorn)
├── render.yaml                # Render Blueprint Deployment Configuration
├── run_windows.bat            # 1-Click Interactive Launcher for Windows
│
├── scripts/                   # CLI Administration & Maintenance Utilities
│   ├── init_db.py             # Schema Initialization & Ground Inventory Seeder
│   └── create_admin.py        # Secure Interactive/CLI Administrator Creator
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── base.html              # Core Layout, Navigation Bar, Flash Alerts & Footer
│   ├── index.html             # Landing Page ("PLAY. BOOK. ENJOY." Hero, Live Stats)
│   ├── venues.html            # Ground Directory with Search & Filtering
│   ├── venue_details.html     # Venue Profile with Interactive Slot Picker Widget
│   ├── bookings.html          # Player Booking History Ledger
│   ├── booking_details.html   # Digital Admission Ticket / Booking Voucher Pass
│   ├── payment.html           # Settlement Mode Selection & Summary
│   ├── login.html             # Player Authentication Portal
│   ├── register.html          # New Player Registration Form
│   ├── profile.html           # Player Profile & Security Management
│   ├── teams.html             # Team Directory & Squad Registration Modal
│   ├── team_details.html      # Squad Roster & Membership Controls
│   ├── matches.html           # Match Fixture Board & Scheduling Modal
│   ├── admin_login.html       # Administrator Console Login
│   ├── admin_dashboard.html   # Admin Overview & Real-time Platform Statistics
│   ├── admin_venues.html      # Admin Football Ground Management & CRUD Modals
│   ├── admin_bookings.html    # Admin Global Bookings Ledger & Status Updater
│   └── admin_users.html       # Admin Player Directory & Role Elevation
│
└── static/                    # Front-end Assets
    ├── css/
    │   ├── style.css          # Core Design System, CSS Variables & Layout
    │   ├── auth.css           # Authentication & Registration Card Styles
    │   └── dashboard.css      # Tables, Admin Views, Passes & Badges
    ├── js/
    │   ├── main.js            # Mobile Menu, Toast Notifications, Modals & CSRF
    │   ├── booking.js         # Slot Availability Fetching, Booking & Cancellation
    │   ├── teams.js           # Squad Search, Creation, Code Joining & Copying
    │   ├── matches.js         # Fixture Filtering & Scheduling Validation
    │   └── admin.js           # Admin Venue Modals, User Roles & Status Updates
    └── images/                # Verified Football Turf Images
        ├── hero_football.jpg  # Stadium Hero Banner
        ├── ryan_vibgyor.jpg   # Ryan Vibgyor KPC Empyrean Turf
        ├── kharghar_arena.jpg # Kharghar Football Arena Turf
        └── sports_hub.jpg     # Navi Mumbai Sports Hub Turf
```

---

## 💻 Beginner-Friendly Windows Setup Guide

### Method 1: 1-Click Launch (Recommended)
1. Extract the downloaded `FanClub_Complete_Project.zip` to a folder on your computer.
2. Double-click **`run_windows.bat`**.
3. The script will automatically:
   - Check for Python 3.10+.
   - Create a virtual environment (`venv`).
   - Install required libraries from `requirements.txt`.
   - Initialize the database with verified grounds.
   - Launch `http://127.0.0.1:5000` in your web browser.

---

### Method 2: Manual Terminal Setup (PowerShell / Command Prompt)

1. **Open PowerShell or Command Prompt** and navigate to the project directory:
   ```powershell
   cd path\to\FanClub_Complete_Project
   ```

2. **Create and Activate a Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Initialize the Database**:
   ```powershell
   python scripts/init_db.py
   ```
   *(This creates `fanclub.db` and populates the 3 verified football venues without any fake accounts.)*

5. **Create Your First Administrator**:
   ```powershell
   python scripts/create_admin.py --name "Ground Manager" --email "manager@yourground.com" --phone "9820011223" --password "StrongAdminPass2026!"
   ```
   *Or simply run `python scripts/create_admin.py` without arguments for an interactive, masked password prompt.*

6. **Start the Flask Application**:
   ```powershell
   python app.py
   ```

7. **Open in Browser**:  
   Visit **`http://127.0.0.1:5000`** in Google Chrome, Microsoft Edge, or Firefox.

---

## 🧪 Running the Automated Test Suite

FanClub includes a comprehensive, isolated test suite that verifies all requirements:

```powershell
python test_fanclub.py
```

### Verified Test Cases:
1. `test_01_new_user_registration`: Tests real server-side player account creation.
2. `test_02_duplicate_email_rejection`: Tests strict rejection of duplicate email registrations.
3. `test_03_password_hashing`: Validates that passwords are saved as cryptographic hashes and never plaintext.
4. `test_04_successful_login`: Validates authentication against database credentials and `/api/me`.
5. `test_05_incorrect_password_rejection`: Tests rejection with clear error message when password does not match.
6. `test_06_logout`: Confirms session termination and unauthenticated state.
7. `test_07_unauthorized_access_prevention`: Ensures unauthenticated users cannot access `/bookings` or `/profile`.
8. `test_08_administrator_access_control`: Confirms players cannot access `/admin/*` or `/api/stats`, while administrators have full access.
9. `test_09_successful_booking_creation`: Tests transactional slot reservation and unique voucher generation.
10. `test_10_duplicate_slot_booking_prevention`: Confirms that double-booking the same venue, date, and slot is strictly blocked.
11. `test_11_booking_history`: Verifies player booking history accurately queries the user's records.
12. `test_12_booking_cancellation`: Tests 1-click slot cancellation and immediate availability re-opening for others.
13. `test_13_database_persistence`: Verifies data integrity and record status across queries.

---

## 🌐 Public Production Deployment Guide

FanClub is designed for immediate cloud deployment on **Render**, **Railway**, **Heroku**, or any Linux VPS. It does **not** rely on your local machine once deployed.

### Environment Variables
Configure the following environment variables in your cloud provider's dashboard:

| Variable Name | Required | Description | Example |
|---|---|---|---|
| `FLASK_ENV` | Yes | Set to `production` for secure cookie flags | `production` |
| `SECRET_KEY` | Yes | 64-character random hex string for session encryption | Run `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | Yes (for persistent DB) | Connection string for PostgreSQL | `postgresql://user:pass@ep-host.render.com/fanclub` |
| `PORT` | Auto | Port provided by host environment | `10000` or `5000` |
| `ADMIN_EMAIL` | Optional | Auto-provisions admin account on container launch | `admin@yourdomain.com` |
| `ADMIN_PASSWORD` | Optional | Auto-provisions admin password on startup | `YourSecurePassword2026!` |

---

### Deploying to Render.com (Recommended Free/Low-Cost)

1. **Push your code to a private GitHub repository**.
2. **Log into Render.com** and click **New +** -> **Blueprint**.
3. Select your repository. Render will automatically read `render.yaml` and:
   - Create a free managed PostgreSQL database (`fanclub-postgres`).
   - Create a Python Web Service running Gunicorn.
   - Run `pip install -r requirements.txt && python scripts/init_db.py`.
   - Start the app with `gunicorn app:app`.
4. Render will provide a public HTTPS URL (e.g., `https://fanclub-football.onrender.com`).

---

### Deploying to Railway.app

1. Click **New Project** -> **Provision PostgreSQL**.
2. Click **Add Service** -> **GitHub Repo**.
3. Under **Variables**, add:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
   - `SECRET_KEY` = your generated secret key
   - `FLASK_ENV` = `production`
4. Railway will automatically detect the `Procfile` and launch your live site.

---

## 🔒 Security Summary

- **CSRF Protection**: All forms utilize server-generated CSRF tokens; asynchronous fetch calls automatically include `X-CSRF-Token`.
- **SQL Injection Prevention**: All queries use SQLAlchemy ORM parameterized statements.
- **Zero Hardcoded Secrets**: Secret keys and database URLs are strictly driven by environment configuration.
- **Role Isolation**: Ground administration requires `role == 'admin'` verified on every server request.
- **Clean Database Delivery**: The repository contains zero sample users, zero demo credentials, and zero mock bookings.
