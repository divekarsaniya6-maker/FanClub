"""
FanClub Platform - Database Initialization & Seed Script
Creates all tables across SQLite or PostgreSQL and seeds verified venues.
Does NOT seed hardcoded user or demo accounts.
"""
import os
import sys

# Ensure project root is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app
from models import db, Venue, User
from werkzeug.security import generate_password_hash

def init_database(verbose=True):
    with app.app_context():
        if verbose:
            print(f"[*] Initializing FanClub database schema at: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Create all tables according to SQLAlchemy models
        db.create_all()
        if verbose:
            print("  [+] All database tables and indexes verified successfully.")

        # Seed verified football venues if table is empty
        if Venue.query.count() == 0:
            venues = [
                Venue(
                    name='Ryan Vibgyor KPC Empyrean',
                    location='Kharghar, Navi Mumbai, Maharashtra',
                    sport='Football',
                    price_per_slot=200.0,
                    image_url='/static/images/ryan_vibgyor.jpg',
                    rating=4.9,
                    facilities='FIFA Standard Synthetic Grass, High-Mast LED Floodlights, Changing Rooms, Dugouts, Spectator Seating, Parking',
                    description='Premier 7v7 football turf situated in Kharghar, featuring tournament-grade synthetic grass, professional night-time floodlights, and spectator seating.',
                    is_active=True
                ),
                Venue(
                    name='Kharghar Football Arena',
                    location='Kharghar, Sector 20, Navi Mumbai',
                    sport='Football',
                    price_per_slot=200.0,
                    image_url='/static/images/kharghar_arena.jpg',
                    rating=4.8,
                    facilities='All-Weather Turf, Perimeter Safety Netting, LED Lighting, Refreshment Lounge, First Aid Support',
                    description='All-weather 7v7 football turf arena designed for fast-paced club matches, community tournaments, and evening team training.',
                    is_active=True
                ),
                Venue(
                    name='Navi Mumbai Sports Hub',
                    location='Panvel, Near Station, Navi Mumbai',
                    sport='Football',
                    price_per_slot=200.0,
                    image_url='/static/images/sports_hub.jpg',
                    rating=4.7,
                    facilities='Lush Synthetic Grass, Dugout Boxes, Perimeter Safety Netting, Changing Lockers, Water Station',
                    description='Spacious multi-sport turf facility located conveniently near Panvel station, offering seamless pitch reservations for football squads.',
                    is_active=True
                )
            ]
            db.session.bulk_save_objects(venues)
            db.session.commit()
            if verbose:
                print("  [+] Seeded 3 verified football turf venues.")
        else:
            if verbose:
                print(f"  [i] Venues already populated ({Venue.query.count()} active venues found).")

        # Check for environment-based administrator auto-provisioning
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin_name = os.environ.get('ADMIN_NAME', 'System Administrator')
        admin_phone = os.environ.get('ADMIN_PHONE', '9876543210')

        if admin_email and admin_password:
            admin_email = admin_email.strip().lower()
            existing_admin = User.query.filter_by(email=admin_email).first()
            if not existing_admin:
                admin_user = User(
                    name=admin_name,
                    email=admin_email,
                    phone=admin_phone,
                    password_hash=generate_password_hash(admin_password),
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                if verbose:
                    print(f"  [+] Provisioned administrator account from environment: {admin_email}")
            else:
                if existing_admin.role != 'admin':
                    existing_admin.role = 'admin'
                    db.session.commit()
                    if verbose:
                        print(f"  [+] Promoted existing user '{admin_email}' to administrator.")

        if verbose:
            print("[*] FanClub database initialization complete!")

if __name__ == '__main__':
    init_database(verbose=True)
