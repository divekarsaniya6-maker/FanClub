import os
import sqlite3
import secrets
from datetime import date, datetime
from functools import wraps
from flask import Flask, g, jsonify, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "fanclub.db")
app = Flask(__name__)
app.secret_key = os.environ.get("FANCLUB_SECRET_KEY", secrets.token_hex(32))
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

VENUE_NAME = "Ryan Vibgyor KPC Empyrean"
VENUE_LOCATION = "Kharghar"
SLOT_PRICE = 200
SLOTS = ["8:00 PM - 9:00 PM", "9:00 PM - 10:00 PM"]

def connect_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    with connect_db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            sport TEXT NOT NULL DEFAULT 'Football',
            venue TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            amount INTEGER NOT NULL DEFAULT 200,
            payment_status TEXT NOT NULL DEFAULT 'Pending',
            booking_status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(venue, booking_date, time_slot),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            captain TEXT NOT NULL,
            city TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL DEFAULT 'Player',
            joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(team_id, user_id),
            FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            match_date TEXT NOT NULL,
            match_time TEXT NOT NULL,
            venue TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Scheduled',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Development admin account. Change the password before deploying publicly.
        admin = con.execute("SELECT id FROM users WHERE email = ?", ("admin@fanclub.local",)).fetchone()
        if not admin:
            con.execute(
                "INSERT INTO users(name,email,phone,password_hash,role) VALUES(?,?,?,?,?)",
                ("FanClub Admin", "admin@fanclub.local", "9999999999",
                 generate_password_hash("FanClub@2026"), "admin")
            )
        # Seed the initial team/match only when no records exist.
        if con.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 0:
            con.execute(
                "INSERT INTO teams(name,captain,city,description,created_by) VALUES(?,?,?,?,?)",
                ("Kharghar Strikers", "FanClub Admin", "Kharghar",
                 "Local footballers who love the game.", 1)
            )
        if con.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0:
            con.execute(
                "INSERT INTO matches(home_team,away_team,match_date,match_time,venue,status) VALUES(?,?,?,?,?,?)",
                ("Kharghar Strikers", "Panvel United", "2026-11-20", "8:00 PM",
                 VENUE_NAME, "Scheduled")
            )

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with connect_db() as con:
        row = con.execute("SELECT id,name,email,phone,role,created_at FROM users WHERE id=?", (uid,)).fetchone()
        return dict(row) if row else None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify(success=False, message="Please log in first."), 401
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify(success=False, message="Please log in first."), 401
        if user["role"] != "admin":
            return jsonify(success=False, message="Admin access required."), 403
        return fn(*args, **kwargs)
    return wrapper

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/login")
def login_page():
    return render_template("index.html", open_auth="login")

@app.get("/register")
def register_page():
    return render_template("index.html", open_auth="register")

@app.get("/admin")
def admin_page():
    return render_template("index.html", open_admin=True)

@app.get("/api/config")
def api_config():
    return jsonify(success=True, venue=VENUE_NAME, location=VENUE_LOCATION, price=SLOT_PRICE, slots=SLOTS)

@app.get("/api/me")
def api_me():
    return jsonify(success=True, user=current_user())

@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    phone = "".join(c for c in str(data.get("phone", "")) if c.isdigit())
    password = str(data.get("password", ""))
    if not name or not email or not phone or not password:
        return jsonify(success=False, message="Please fill in every field."), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify(success=False, message="Enter a valid email address."), 400
    if len(phone) < 10 or len(phone) > 15:
        return jsonify(success=False, message="Enter a valid phone number."), 400
    if len(password) < 8:
        return jsonify(success=False, message="Password must be at least 8 characters."), 400
    try:
        with connect_db() as con:
            cur = con.execute(
                "INSERT INTO users(name,email,phone,password_hash) VALUES(?,?,?,?)",
                (name, email, phone, generate_password_hash(password))
            )
            uid = cur.lastrowid
            con.execute("INSERT INTO team_members(team_id,user_id,role) SELECT id, ?, 'Player' FROM teams WHERE name='Kharghar Strikers'", (uid,))
        session["user_id"] = uid
        return jsonify(success=True, message="Account created. Welcome to FanClub!", user=current_user())
    except sqlite3.IntegrityError:
        return jsonify(success=False, message="An account with this email already exists."), 409

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    with connect_db() as con:
        row = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(success=False, message="Incorrect email or password."), 401
    session.clear()
    session["user_id"] = row["id"]
    return jsonify(success=True, message="Login successful.", user=current_user())

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(success=True, message="You have logged out.")

@app.get("/api/bookings")
@login_required
def list_bookings():
    user = current_user()
    with connect_db() as con:
        if user["role"] == "admin" and request.args.get("all") == "1":
            rows = con.execute("SELECT * FROM bookings ORDER BY booking_date DESC, id DESC").fetchall()
        else:
            rows = con.execute("SELECT * FROM bookings WHERE user_id=? ORDER BY booking_date DESC, id DESC", (user["id"],)).fetchall()
    return jsonify(success=True, bookings=[dict(r) for r in rows])

@app.post("/api/bookings")
@login_required
def create_booking():
    data = request.get_json(silent=True) or {}
    user = current_user()
    name = str(data.get("name") or user["name"]).strip()
    phone = "".join(c for c in str(data.get("phone") or user["phone"]) if c.isdigit())
    booking_date = str(data.get("date", ""))
    time_slot = str(data.get("time_slot", ""))
    if not name or len(phone) < 10 or len(phone) > 15:
        return jsonify(success=False, message="Enter a name and valid phone number."), 400
    try:
        chosen = date.fromisoformat(booking_date)
        if chosen < date.today():
            return jsonify(success=False, message="You cannot book a date in the past."), 400
    except ValueError:
        return jsonify(success=False, message="Choose a valid date."), 400
    if time_slot not in SLOTS:
        return jsonify(success=False, message="Choose an available time slot."), 400
    try:
        with connect_db() as con:
            cur = con.execute(
                """INSERT INTO bookings(user_id,name,phone,sport,venue,booking_date,time_slot,amount,payment_status,booking_status)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (user["id"], name, phone, "Football", VENUE_NAME, booking_date, time_slot, SLOT_PRICE, "Pending", "Confirmed")
            )
            booking_id = cur.lastrowid
        return jsonify(success=True, message="Slot reserved. Complete the simulated payment.", booking_id=booking_id)
    except sqlite3.IntegrityError:
        return jsonify(success=False, message="This slot is already booked. Please choose another slot."), 409

@app.post("/api/payment")
@login_required
def pay():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    method = str(data.get("method", "UPI"))
    if method not in ["UPI", "Card", "Cash at Venue"]:
        return jsonify(success=False, message="Select a valid payment method."), 400
    with connect_db() as con:
        row = con.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        user = current_user()
        if not row:
            return jsonify(success=False, message="Booking not found."), 404
        if row["user_id"] != user["id"] and user["role"] != "admin":
            return jsonify(success=False, message="You cannot pay for this booking."), 403
        status = "Pay at venue" if method == "Cash at Venue" else "Simulated successful"
        con.execute("UPDATE bookings SET payment_status=? WHERE id=?", (status, booking_id))
    return jsonify(success=True, message="Demo payment recorded. No real money was charged.", booking_id=booking_id, payment_status=status)

@app.post("/api/bookings/<int:booking_id>/cancel")
@login_required
def cancel_booking(booking_id):
    user = current_user()
    with connect_db() as con:
        row = con.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not row:
            return jsonify(success=False, message="Booking not found."), 404
        if row["user_id"] != user["id"] and user["role"] != "admin":
            return jsonify(success=False, message="You cannot cancel this booking."), 403
        con.execute("UPDATE bookings SET booking_status='Cancelled' WHERE id=?", (booking_id,))
    return jsonify(success=True, message="Booking cancelled.")

@app.get("/api/teams")
def list_teams():
    with connect_db() as con:
        rows = con.execute("""
            SELECT t.*, COUNT(tm.user_id) AS member_count
            FROM teams t LEFT JOIN team_members tm ON tm.team_id=t.id
            GROUP BY t.id ORDER BY t.created_at DESC
        """).fetchall()
    return jsonify(success=True, teams=[dict(r) for r in rows])

@app.post("/api/teams")
@login_required
def create_team():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    city = str(data.get("city", "")).strip()
    description = str(data.get("description", "")).strip()
    user = current_user()
    if not name or not city:
        return jsonify(success=False, message="Team name and city are required."), 400
    try:
        with connect_db() as con:
            cur = con.execute(
                "INSERT INTO teams(name,captain,city,description,created_by) VALUES(?,?,?,?,?)",
                (name, user["name"], city, description, user["id"])
            )
            con.execute("INSERT INTO team_members(team_id,user_id,role) VALUES(?,?,'Captain')", (cur.lastrowid, user["id"]))
        return jsonify(success=True, message="Team created successfully.")
    except sqlite3.IntegrityError:
        return jsonify(success=False, message="A team with that name already exists."), 409

@app.post("/api/teams/<int:team_id>/join")
@login_required
def join_team(team_id):
    user = current_user()
    try:
        with connect_db() as con:
            con.execute("INSERT INTO team_members(team_id,user_id,role) VALUES(?,?,'Player')", (team_id, user["id"]))
        return jsonify(success=True, message="You joined the team.")
    except sqlite3.IntegrityError:
        return jsonify(success=False, message="You are already in this team, or the team does not exist."), 409

@app.post("/api/teams/<int:team_id>/leave")
@login_required
def leave_team(team_id):
    user = current_user()
    with connect_db() as con:
        row = con.execute("SELECT role FROM team_members WHERE team_id=? AND user_id=?", (team_id, user["id"])).fetchone()
        if not row:
            return jsonify(success=False, message="You are not a member of this team."), 404
        if row["role"] == "Captain":
            return jsonify(success=False, message="The captain cannot leave without transferring captaincy."), 400
        con.execute("DELETE FROM team_members WHERE team_id=? AND user_id=?", (team_id, user["id"]))
    return jsonify(success=True, message="You left the team.")

@app.get("/api/teams/<int:team_id>/members")
def team_members(team_id):
    with connect_db() as con:
        rows = con.execute("""
            SELECT u.id,u.name,u.email,tm.role,tm.joined_at
            FROM team_members tm JOIN users u ON u.id=tm.user_id
            WHERE tm.team_id=? ORDER BY CASE tm.role WHEN 'Captain' THEN 0 ELSE 1 END, u.name
        """, (team_id,)).fetchall()
    return jsonify(success=True, members=[dict(r) for r in rows])

@app.get("/api/matches")
def list_matches():
    with connect_db() as con:
        rows = con.execute("SELECT * FROM matches ORDER BY match_date, match_time").fetchall()
    return jsonify(success=True, matches=[dict(r) for r in rows])

@app.post("/api/matches")
@admin_required
def create_match():
    data = request.get_json(silent=True) or {}
    home = str(data.get("home_team", "")).strip()
    away = str(data.get("away_team", "")).strip()
    md = str(data.get("match_date", ""))
    mt = str(data.get("match_time", "")).strip()
    venue = str(data.get("venue", VENUE_NAME)).strip()
    if not home or not away or not md or not mt or not venue:
        return jsonify(success=False, message="Please complete every match field."), 400
    if home.lower() == away.lower():
        return jsonify(success=False, message="A team cannot play against itself."), 400
    try:
        if date.fromisoformat(md) < date.today():
            return jsonify(success=False, message="Match date cannot be in the past."), 400
    except ValueError:
        return jsonify(success=False, message="Choose a valid match date."), 400
    with connect_db() as con:
        con.execute("INSERT INTO matches(home_team,away_team,match_date,match_time,venue,created_by) VALUES(?,?,?,?,?,?)",
                    (home, away, md, mt, venue, current_user()["id"]))
    return jsonify(success=True, message="Match scheduled.")

@app.delete("/api/matches/<int:match_id>")
@admin_required
def delete_match(match_id):
    with connect_db() as con:
        con.execute("DELETE FROM matches WHERE id=?", (match_id,))
    return jsonify(success=True, message="Match deleted.")

@app.get("/api/profile")
@login_required
def profile():
    user = current_user()
    with connect_db() as con:
        bookings = con.execute("SELECT COUNT(*) FROM bookings WHERE user_id=?", (user["id"],)).fetchone()[0]
        teams = con.execute("SELECT COUNT(*) FROM team_members WHERE user_id=?", (user["id"],)).fetchone()[0]
    return jsonify(success=True, profile={**user, "bookings_count": bookings, "teams_count": teams})

@app.put("/api/profile")
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    phone = "".join(c for c in str(data.get("phone", "")) if c.isdigit())
    if not name or len(phone) < 10 or len(phone) > 15:
        return jsonify(success=False, message="Enter a name and valid phone number."), 400
    with connect_db() as con:
        con.execute("UPDATE users SET name=?,phone=? WHERE id=?", (name, phone, session["user_id"]))
        con.execute("UPDATE bookings SET name=?,phone=? WHERE user_id=? AND booking_status='Confirmed'", (name, phone, session["user_id"]))
    return jsonify(success=True, message="Profile updated.")

@app.get("/api/admin/stats")
@admin_required
def admin_stats():
    with connect_db() as con:
        users = con.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
        bookings = con.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        teams = con.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        matches = con.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        revenue = con.execute("SELECT COALESCE(SUM(amount),0) FROM bookings WHERE payment_status='Simulated successful'").fetchone()[0]
    return jsonify(success=True, stats={"users": users, "bookings": bookings, "teams": teams, "matches": matches, "revenue": revenue})

@app.get("/api/admin/users")
@admin_required
def admin_users():
    with connect_db() as con:
        rows = con.execute("SELECT id,name,email,phone,role,created_at FROM users ORDER BY id DESC").fetchall()
    return jsonify(success=True, users=[dict(r) for r in rows])

@app.delete("/api/admin/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    if user_id == session.get("user_id"):
        return jsonify(success=False, message="You cannot delete your own admin account."), 400
    with connect_db() as con:
        con.execute("DELETE FROM users WHERE id=? AND role!='admin'", (user_id,))
    return jsonify(success=True, message="User deleted if the account existed.")

@app.get("/api/admin/bookings")
@admin_required
def admin_bookings():
    with connect_db() as con:
        rows = con.execute("SELECT * FROM bookings ORDER BY created_at DESC").fetchall()
    return jsonify(success=True, bookings=[dict(r) for r in rows])

@app.get("/api/admin/teams")
@admin_required
def admin_teams():
    with connect_db() as con:
        rows = con.execute("SELECT * FROM teams ORDER BY id DESC").fetchall()
    return jsonify(success=True, teams=[dict(r) for r in rows])

@app.delete("/api/admin/teams/<int:team_id>")
@admin_required
def admin_delete_team(team_id):
    with connect_db() as con:
        con.execute("DELETE FROM teams WHERE id=?", (team_id,))
    return jsonify(success=True, message="Team deleted if it existed.")

@app.post("/api/admin/bookings/<int:booking_id>/cancel")
@admin_required
def admin_cancel_booking(booking_id):
    with connect_db() as con:
        con.execute("UPDATE bookings SET booking_status='Cancelled' WHERE id=?", (booking_id,))
    return jsonify(success=True, message="Booking cancelled if it existed.")

@app.get("/api/admin/matches")
@admin_required
def admin_matches():
    return list_matches()

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify(success=False, message="Endpoint not found."), 404
    return "Page not found", 404

@app.errorhandler(500)
def server_error(_):
    if request.path.startswith("/api/"):
        return jsonify(success=False, message="Unexpected server error. Check the terminal for details."), 500
    return "Unexpected server error. Check the terminal.", 500

if __name__ == "__main__":
    init_db()
    print("\\nFanClub is starting...")
    print("Open http://127.0.0.1:5000")
    print("Development admin: admin@fanclub.local / FanClub@2026")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
