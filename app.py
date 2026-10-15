"""
FanClub – Professional Football Ground Booking & Community Platform
Production-Ready Flask Web Application
"""
import os
import re
import secrets
from datetime import datetime, date, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Venue, Booking, Team, TeamMember, Match

# -------------------------------------------------------------
# App Initialization & Environment Configuration
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder='static', template_folder='templates')

# Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fanclub-dev-secret-key-change-in-production-2026')

# Database Configuration (Supports PostgreSQL for production & SQLite for local development)
raw_db_url = os.environ.get('DATABASE_URL')
if raw_db_url:
    # Handle Render/Heroku 'postgres://' quirk
    if raw_db_url.startswith('postgres://'):
        raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = raw_db_url
else:
    local_db_path = os.path.join(BASE_DIR, 'fanclub.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{local_db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security & Session Settings
is_prod = (os.environ.get('FLASK_ENV') == 'production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = is_prod
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize SQLAlchemy
db.init_app(app)

# Standard IST Timezone
IST = ZoneInfo("Asia/Kolkata")

def get_ist_now():
    return datetime.now(IST)

def get_ist_today_str():
    return get_ist_now().strftime("%Y-%m-%d")

# Standard 1-Hour Ground Time Slots
STANDARD_SLOTS = [
    "6:00 AM – 7:00 AM",
    "7:00 AM – 8:00 AM",
    "8:00 AM – 9:00 AM",
    "9:00 AM – 10:00 AM",
    "4:00 PM – 5:00 PM",
    "5:00 PM – 6:00 PM",
    "6:00 PM – 7:00 PM",
    "7:00 PM – 8:00 PM",
    "8:00 PM – 9:00 PM",
    "9:00 PM – 10:00 PM",
    "10:00 PM – 11:00 PM"
]

# -------------------------------------------------------------
# Database Setup Helper
# -------------------------------------------------------------
with app.app_context():
    db.create_all()
    # Check if venues exist; if not, seed initial inventory
    if Venue.query.count() == 0:
        from scripts.init_db import init_database
        init_database(verbose=False)

# -------------------------------------------------------------
# CSRF Protection & Context Processors
# -------------------------------------------------------------
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(24)
    return session['_csrf_token']

@app.context_processor
def inject_global_vars():
    return {
        'csrf_token': generate_csrf_token(),
        'current_year': get_ist_now().year,
        'today_date': get_ist_today_str()
    }

def verify_csrf(req):
    token = req.form.get('csrf_token') or req.headers.get('X-CSRF-Token')
    expected = session.get('_csrf_token')
    if not expected or not token or token != expected:
        return False
    return True

# -------------------------------------------------------------
# Authentication & Authorization Decorators
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
            flash('Please sign in to access your account.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Administrator authentication required.'}), 401
            flash('Administrator authentication required.', 'danger')
            return redirect(url_for('admin_login', next=request.path))

        user = db.session.get(User, session['user_id'])
        if not user or user.role != 'admin':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Access forbidden: Administrator privileges required.'}), 403
            flash('Access restricted to administrators only.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------------------------------
# Public & General Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    total_users = User.query.filter_by(role='user').count()
    total_venues = Venue.query.filter_by(is_active=True).count()
    total_bookings = Booking.query.filter_by(status='Confirmed').count()
    total_teams = Team.query.count()

    featured_venues = Venue.query.filter_by(is_active=True).order_by(Venue.id.asc()).limit(3).all()

    stats = {
        'total_users': total_users,
        'total_venues': total_venues,
        'total_bookings': total_bookings,
        'total_teams': total_teams
    }
    return render_template('index.html', stats=stats, featured_venues=featured_venues, active_page='home')

@app.route('/venues')
def venues():
    all_venues = Venue.query.filter_by(is_active=True).order_by(Venue.id.asc()).all()
    return render_template('venues.html', venues=all_venues, active_page='venues')

@app.route('/venues/<int:venue_id>')
def venue_details(venue_id):
    venue = db.session.get(Venue, venue_id)
    if not venue or not venue.is_active:
        flash('Requested football venue could not be found or is inactive.', 'error')
        return redirect(url_for('venues'))
    return render_template('venue_details.html', venue=venue, active_page='venues')

# -------------------------------------------------------------
# User Authentication Routes
# -------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not verify_csrf(request):
            flash('Session expired or invalid token. Please try again.', 'error')
            return redirect(url_for('login'))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both your email address and password.', 'error')
            return render_template('login.html', active_page='login')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session.permanent = remember
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_role'] = user.role
            session['user_phone'] = user.phone

            flash(f'Welcome back, {user.name}!', 'success')
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('bookings'))
        else:
            flash('Invalid email address or password. Please verify your credentials.', 'error')

    return render_template('login.html', active_page='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if not verify_csrf(request):
            flash('Session expired. Please try registering again.', 'error')
            return redirect(url_for('register'))

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Strict Server-Side Validation
        if not name or len(name) < 2:
            flash('Please enter your full name (minimum 2 characters).', 'error')
            return render_template('register.html', active_page='register')

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            flash('Please provide a valid email address.', 'error')
            return render_template('register.html', active_page='register')

        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
        if len(clean_phone) < 10 or not clean_phone.isdigit():
            flash('Please enter a valid mobile phone number (at least 10 digits).', 'error')
            return render_template('register.html', active_page='register')

        if len(password) < 8:
            flash('Password must be at least 8 characters long for account security.', 'error')
            return render_template('register.html', active_page='register')

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter them carefully.', 'error')
            return render_template('register.html', active_page='register')

        # Check for duplicate email
        if User.query.filter_by(email=email).first():
            flash('An account with this email address is already registered. Please sign in.', 'warning')
            return redirect(url_for('login'))

        # Create new player account (Strictly role='user')
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role='user'
        )
        db.session.add(new_user)
        db.session.commit()

        # Establish authenticated session
        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        session['user_email'] = new_user.email
        session['user_role'] = 'user'
        session['user_phone'] = new_user.phone

        flash('Your player account has been created successfully! Welcome to FanClub.', 'success')
        return redirect(url_for('venues'))

    return render_template('register.html', active_page='register')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    booking_count = Booking.query.filter_by(user_id=user.id).count()
    teams_count = TeamMember.query.filter_by(user_id=user.id).count()

    stats = {
        'total_bookings': booking_count,
        'teams_count': teams_count
    }
    return render_template('profile.html', user=user, stats=stats, active_page='profile')

@app.route('/profile/update', methods=['POST'])
@login_required
def profile_update():
    if not verify_csrf(request):
        flash('Invalid session token.', 'error')
        return redirect(url_for('profile'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not name or len(name) < 2 or not phone:
        flash('Valid name and phone number are required.', 'error')
        return redirect(url_for('profile'))

    user = db.session.get(User, session['user_id'])
    if user:
        user.name = name
        user.phone = phone
        db.session.commit()

        session['user_name'] = name
        session['user_phone'] = phone
        flash('Your profile contact details have been updated.', 'success')

    return redirect(url_for('profile'))

@app.route('/profile/change-password', methods=['POST'])
@login_required
def profile_password():
    if not verify_csrf(request):
        flash('Invalid session token.', 'error')
        return redirect(url_for('profile'))

    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_new_password', '')

    if len(new_pw) < 8:
        flash('New password must be at least 8 characters long.', 'error')
        return redirect(url_for('profile'))

    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile'))

    user = db.session.get(User, session['user_id'])
    if not user or not check_password_hash(user.password_hash, current_pw):
        flash('Current password entered is incorrect.', 'error')
        return redirect(url_for('profile'))

    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()

    flash('Account password updated successfully!', 'success')
    return redirect(url_for('profile'))

# -------------------------------------------------------------
# Football Ground Booking System
# -------------------------------------------------------------
@app.route('/api/venues/<int:venue_id>/slots')
def api_venue_slots(venue_id):
    booking_date = request.args.get('date', '').strip()
    if not booking_date:
        booking_date = get_ist_today_str()

    venue = db.session.get(Venue, venue_id)
    if not venue or not venue.is_active:
        return jsonify({'error': 'Venue not found or inactive'}), 404

    # Query active bookings for the specified date and venue
    active_bookings = Booking.query.filter(
        Booking.venue_id == venue_id,
        Booking.booking_date == booking_date,
        Booking.status != 'Cancelled'
    ).all()

    booked_slots = {b.time_slot for b in active_bookings}

    slots_response = []
    for slot in STANDARD_SLOTS:
        slots_response.append({
            'time': slot,
            'is_available': (slot not in booked_slots)
        })

    return jsonify({
        'venue_id': venue_id,
        'venue_name': venue.name,
        'date': booking_date,
        'slots': slots_response
    })

@app.route('/bookings/create', methods=['POST'])
def booking_create():
    data = request.get_json() if request.is_json else request.form

    venue_id = data.get('venue_id')
    booking_date = data.get('date', '').strip()
    time_slot = data.get('time_slot', '').strip()
    contact_name = data.get('contact_name', '').strip()
    contact_phone = data.get('contact_phone', '').strip()

    if not venue_id or not booking_date or not time_slot or not contact_name or not contact_phone:
        return jsonify({'success': False, 'message': 'All booking fields are required.'}), 400

    today_ist = get_ist_today_str()
    if booking_date < today_ist:
        return jsonify({'success': False, 'message': 'Bookings cannot be made for past dates.'}), 400

    venue = db.session.get(Venue, venue_id)
    if not venue or not venue.is_active:
        return jsonify({'success': False, 'message': 'Selected venue is unavailable.'}), 404

    # Server-Side Double-Booking Prevention (Transactional Check)
    existing_booking = Booking.query.filter(
        Booking.venue_id == venue.id,
        Booking.booking_date == booking_date,
        Booking.time_slot == time_slot,
        Booking.status != 'Cancelled'
    ).first()

    if existing_booking:
        return jsonify({
            'success': False,
            'message': f'This slot ({time_slot}) on {booking_date} has already been booked. Please pick an alternative time slot.'
        }), 400

    # User association (if signed in)
    user_id = session.get('user_id')
    booking_code = f"FC-2026-{secrets.token_hex(3).upper()}"

    new_booking = Booking(
        booking_code=booking_code,
        user_id=user_id,
        venue_id=venue.id,
        venue_name=venue.name,
        location=venue.location,
        booking_date=booking_date,
        time_slot=time_slot,
        amount=venue.price_per_slot,
        contact_name=contact_name,
        contact_phone=contact_phone,
        payment_status='Pending (Desk Settlement)',
        payment_method='Pay at Venue',
        status='Confirmed'
    )

    db.session.add(new_booking)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Could not complete booking: {str(e)}'}), 500

    flash(f'Ground reservation confirmed! Your booking ID is {booking_code}.', 'success')
    return jsonify({
        'success': True,
        'booking_id': new_booking.id,
        'booking_code': booking_code,
        'redirect': url_for('booking_details', booking_id=new_booking.id)
    })

@app.route('/bookings')
@login_required
def bookings():
    user_id = session['user_id']
    user_bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.id.desc()).all()
    return render_template('bookings.html', bookings=user_bookings, active_page='bookings')

@app.route('/bookings/<int:booking_id>')
def booking_details(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        flash('Booking record not found.', 'error')
        return redirect(url_for('venues'))

    # Authorization Check: Logged in owner or administrator
    if booking.user_id and session.get('user_id'):
        if booking.user_id != session['user_id'] and session.get('user_role') != 'admin':
            flash('Access denied: You do not have permission to view this reservation.', 'error')
            return redirect(url_for('bookings'))

    return render_template('booking_details.html', booking=booking, active_page='bookings')

@app.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def booking_cancel(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found.'}), 404

    user_id = session.get('user_id')
    is_admin = (session.get('user_role') == 'admin')
    is_owner = (booking.user_id is not None and booking.user_id == user_id)

    # Allow cancellation if user is the booking owner, or user is an admin
    if not is_owner and not is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized action.'}), 403

    if booking.status == 'Cancelled':
        return jsonify({'success': False, 'message': 'Booking is already cancelled.'}), 400

    booking.status = 'Cancelled'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Booking cancelled successfully. The pitch slot has been released.'
    })

# -------------------------------------------------------------
# Teams & Squad Management
# -------------------------------------------------------------
@app.route('/teams')
def teams():
    all_teams = Team.query.order_by(Team.name.asc()).all()
    return render_template('teams.html', teams=all_teams, active_page='teams')

@app.route('/teams/<int:team_id>')
def team_details(team_id):
    team = db.session.get(Team, team_id)
    if not team:
        flash('Team not found.', 'error')
        return redirect(url_for('teams'))

    members = TeamMember.query.filter_by(team_id=team_id).order_by(TeamMember.role.desc(), TeamMember.joined_at.asc()).all()

    user_id = session.get('user_id')
    is_member = any(m.user_id == user_id for m in members) if user_id else False
    is_captain = (team.captain_id == user_id) if user_id else False

    return render_template('team_details.html', team=team, members=members, is_member=is_member, is_captain=is_captain, active_page='teams')

@app.route('/teams/create', methods=['POST'])
@login_required
def team_create():
    data = request.get_json() if request.is_json else request.form
    name = data.get('name', '').strip()
    city = data.get('city', '').strip()
    description = data.get('description', '').strip()

    if not name or len(name) < 2 or not city:
        return jsonify({'success': False, 'message': 'Valid squad name and home city are required.'}), 400

    if Team.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': 'A football team with this name already exists.'}), 400

    slug = re.sub(r'[^A-Z]', '', name.upper())[:4] or 'TEAM'
    team_code = f"FC-{slug}-{secrets.token_hex(2).upper()}"

    new_team = Team(
        name=name,
        team_code=team_code,
        captain_id=session['user_id'],
        captain_name=session['user_name'],
        city=city,
        description=description
    )
    db.session.add(new_team)
    db.session.flush()

    # Add creator as Captain
    captain_member = TeamMember(
        team_id=new_team.id,
        user_id=session['user_id'],
        role='Captain'
    )
    db.session.add(captain_member)
    db.session.commit()

    return jsonify({
        'success': True,
        'team_id': new_team.id,
        'team_code': team_code,
        'redirect': url_for('team_details', team_id=new_team.id)
    })

@app.route('/teams/<int:team_id>/join', methods=['POST'])
@login_required
def team_join(team_id):
    team = db.session.get(Team, team_id)
    if not team:
        return jsonify({'success': False, 'message': 'Team not found.'}), 404

    user_id = session['user_id']
    if TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first():
        return jsonify({'success': False, 'message': 'You are already registered in this squad.'}), 400

    new_member = TeamMember(team_id=team_id, user_id=user_id, role='Player')
    db.session.add(new_member)
    db.session.commit()

    return jsonify({'success': True, 'message': f'You have joined {team.name}!'})

@app.route('/teams/join-code', methods=['POST'])
@login_required
def team_join_code():
    data = request.get_json() if request.is_json else request.form
    code = data.get('team_code', '').strip().upper()

    if not code:
        return jsonify({'success': False, 'message': 'Team code is required.'}), 400

    team = Team.query.filter_by(team_code=code).first()
    if not team:
        return jsonify({'success': False, 'message': 'Invalid squad code. Team not found.'}), 404

    user_id = session['user_id']
    if TeamMember.query.filter_by(team_id=team.id, user_id=user_id).first():
        return jsonify({'success': False, 'message': f'You are already a member of {team.name}.'}), 400

    new_member = TeamMember(team_id=team.id, user_id=user_id, role='Player')
    db.session.add(new_member)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Successfully joined {team.name}!',
        'team_id': team.id,
        'redirect': url_for('team_details', team_id=team.id)
    })

@app.route('/teams/<int:team_id>/leave', methods=['POST'])
@login_required
def team_leave(team_id):
    team = db.session.get(Team, team_id)
    if not team:
        return jsonify({'success': False, 'message': 'Team not found.'}), 404

    user_id = session['user_id']
    if team.captain_id == user_id:
        return jsonify({'success': False, 'message': 'The Team Captain cannot leave the team.'}), 400

    membership = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not membership:
        return jsonify({'success': False, 'message': 'You are not a member of this squad.'}), 400

    db.session.delete(membership)
    db.session.commit()

    return jsonify({'success': True, 'message': 'You have left the squad.'})

# -------------------------------------------------------------
# Football Match Scheduling
# -------------------------------------------------------------
@app.route('/matches')
def matches():
    all_matches = Match.query.order_by(Match.match_date.asc(), Match.match_time.asc()).all()
    all_teams = Team.query.order_by(Team.name.asc()).all()

    user_teams = []
    if session.get('user_id'):
        memberships = TeamMember.query.filter_by(user_id=session['user_id']).all()
        user_team_ids = [m.team_id for m in memberships]
        user_teams = Team.query.filter(Team.id.in_(user_team_ids)).all() if user_team_ids else []

    active_venues = Venue.query.filter_by(is_active=True).order_by(Venue.name.asc()).all()

    return render_template(
        'matches.html',
        matches=all_matches,
        all_teams=all_teams,
        user_teams=user_teams,
        venues=active_venues,
        active_page='matches'
    )

@app.route('/matches/create', methods=['POST'])
@login_required
def match_create():
    data = request.get_json() if request.is_json else request.form

    home_team_id = data.get('home_team_id')
    away_team_id = data.get('away_team_id')
    venue_id = data.get('venue_id')
    match_date = data.get('match_date', '').strip()
    match_time = data.get('match_time', '').strip()
    notes = data.get('notes', '').strip()

    if not home_team_id or not away_team_id or not venue_id or not match_date or not match_time:
        return jsonify({'success': False, 'message': 'All fixture fields are required.'}), 400

    if str(home_team_id) == str(away_team_id):
        return jsonify({'success': False, 'message': 'Home team and Opposing team cannot be identical.'}), 400

    if match_date < get_ist_today_str():
        return jsonify({'success': False, 'message': 'Matches cannot be scheduled for past dates.'}), 400

    new_match = Match(
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        venue_id=venue_id,
        match_date=match_date,
        match_time=match_time,
        status='Scheduled',
        notes=notes,
        created_by_user_id=session['user_id']
    )
    db.session.add(new_match)
    db.session.commit()

    return jsonify({'success': True, 'match_id': new_match.id, 'message': 'Match fixture scheduled successfully!'})

# -------------------------------------------------------------
# Administrator Portal & Management
# -------------------------------------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if not verify_csrf(request):
            flash('Invalid session token.', 'error')
            return redirect(url_for('admin_login'))

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            if user.role != 'admin':
                flash('Access denied: Administrator privileges required.', 'danger')
                return render_template('admin_login.html', active_page='admin')

            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_role'] = 'admin'
            session['user_phone'] = user.phone

            flash('Administrator authenticated successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid administrator credentials.', 'error')

    return render_template('admin_login.html', active_page='admin')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_venues = Venue.query.filter_by(is_active=True).count()
    total_bookings = Booking.query.count()
    total_revenue = db.session.query(db.func.coalesce(db.func.sum(Booking.amount), 0.0)).filter(Booking.status != 'Cancelled').scalar()
    total_matches = Match.query.count()

    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(10).all()

    stats = {
        'total_users': total_users,
        'total_venues': total_venues,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'total_matches': total_matches
    }
    return render_template('admin_dashboard.html', stats=stats, recent_bookings=recent_bookings, active_page='admin')

@app.route('/admin/venues')
@admin_required
def admin_venues():
    all_venues = Venue.query.order_by(Venue.id.asc()).all()
    return render_template('admin_venues.html', venues=all_venues, active_page='admin')

@app.route('/admin/venues/create', methods=['POST'])
@admin_required
def admin_venue_create():
    data = request.get_json() if request.is_json else request.form

    name = data.get('name', '').strip()
    location = data.get('location', '').strip()
    price = float(data.get('price_per_slot', 200.0))
    facilities = data.get('facilities', '').strip()
    description = data.get('description', '').strip()
    image_url = data.get('image_url', '').strip() or '/static/images/ryan_vibgyor.jpg'

    if not name or not location:
        return jsonify({'success': False, 'message': 'Venue name and location are required.'}), 400

    if Venue.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': 'A venue with this name already exists.'}), 400

    new_venue = Venue(
        name=name,
        location=location,
        sport='Football',
        price_per_slot=price,
        image_url=image_url,
        facilities=facilities,
        description=description,
        is_active=True
    )
    db.session.add(new_venue)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Ground venue added successfully!'})

@app.route('/admin/venues/<int:venue_id>/edit', methods=['POST'])
@admin_required
def admin_venue_edit(venue_id):
    data = request.get_json() if request.is_json else request.form
    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({'success': False, 'message': 'Venue not found.'}), 404

    venue.name = data.get('name', venue.name).strip()
    venue.location = data.get('location', venue.location).strip()
    venue.price_per_slot = float(data.get('price_per_slot', venue.price_per_slot))
    venue.facilities = data.get('facilities', venue.facilities).strip()
    venue.description = data.get('description', venue.description).strip()
    if data.get('image_url'):
        venue.image_url = data.get('image_url').strip()

    db.session.commit()
    return jsonify({'success': True, 'message': 'Venue updated successfully.'})

@app.route('/admin/venues/<int:venue_id>/toggle-status', methods=['POST'])
@admin_required
def admin_venue_toggle_status(venue_id):
    venue = db.session.get(Venue, venue_id)
    if not venue:
        return jsonify({'success': False, 'message': 'Venue not found.'}), 404

    venue.is_active = not venue.is_active
    db.session.commit()

    return jsonify({'success': True, 'new_status': int(venue.is_active)})

@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    all_bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template('admin_bookings.html', bookings=all_bookings, active_page='admin')

@app.route('/admin/bookings/<int:booking_id>/update-status', methods=['POST'])
@admin_required
def admin_booking_update_status(booking_id):
    data = request.get_json() if request.is_json else request.form
    new_status = data.get('status', '').strip()

    if new_status not in ['Confirmed', 'Completed', 'Cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status.'}), 400

    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found.'}), 404

    booking.status = new_status
    db.session.commit()

    return jsonify({'success': True, 'message': f'Status updated to {new_status}.'})

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.id.desc()).all()
    # Compute booking counts per user
    user_list = []
    for u in users:
        b_count = Booking.query.filter_by(user_id=u.id).count()
        user_list.append({
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'phone': u.phone,
            'role': u.role,
            'created_at': u.created_at.strftime('%Y-%m-%d'),
            'booking_count': b_count
        })
    return render_template('admin_users.html', users=user_list, active_page='admin')

@app.route('/admin/users/<int:user_id>/toggle-role', methods=['POST'])
@admin_required
def admin_user_toggle_role(user_id):
    data = request.get_json() if request.is_json else request.form
    new_role = data.get('role', 'user').strip()

    if new_role not in ['admin', 'user']:
        return jsonify({'success': False, 'message': 'Invalid role.'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    if user.id == session.get('user_id'):
        return jsonify({'success': False, 'message': 'Cannot modify your own administrative role.'}), 400

    user.role = new_role
    db.session.commit()

    return jsonify({'success': True, 'message': f'Role updated to {new_role}.'})

# -------------------------------------------------------------
# REST API Endpoints for Integration & Testing
# -------------------------------------------------------------
@app.route('/api/venues')
def api_venues():
    venues_list = Venue.query.filter_by(is_active=True).all()
    return jsonify({'venues': [v.to_dict() for v in venues_list]})

@app.route('/api/stats')
@admin_required
def api_stats():
    u_count = User.query.count()
    v_count = Venue.query.count()
    b_count = Booking.query.count()
    t_count = Team.query.count()
    rev = db.session.query(db.func.coalesce(db.func.sum(Booking.amount), 0.0)).filter(Booking.status != 'Cancelled').scalar()

    return jsonify({
        'stats': {
            'total_users': u_count,
            'total_venues': v_count,
            'total_bookings': b_count,
            'total_teams': t_count,
            'revenue': rev
        }
    })

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()

    if not name or not email or not phone or not password:
        return jsonify({'success': False, 'message': 'Missing required registration fields.'}), 400

    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters long.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'User with this email is already registered.'}), 400

    new_user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        role='user'
    )
    db.session.add(new_user)
    db.session.commit()

    session['user_id'] = new_user.id
    session['user_name'] = new_user.name
    session['user_email'] = new_user.email
    session['user_role'] = 'user'
    session['user_phone'] = new_user.phone

    return jsonify({'success': True, 'user_id': new_user.id}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['user_role'] = user.role
        session['user_phone'] = user.phone
        return jsonify({'success': True, 'user': user.to_dict()})
    return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

@app.route('/api/me')
def api_me():
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 401
    user = db.session.get(User, session['user_id'])
    if not user:
        session.clear()
        return jsonify({'authenticated': False}), 401
    return jsonify({
        'authenticated': True,
        'user': user.to_dict()
    })

# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('base.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=(os.environ.get('FLASK_ENV') != 'production'))
