"""
FanClub Automated Comprehensive Test Suite
Validates all requirements specified in Section 10:
- New user registration
- Duplicate email rejection
- Password hashing
- Successful login
- Incorrect password rejection
- Logout
- Unauthorized access prevention
- Administrator access control
- Successful booking creation
- Duplicate slot booking prevention
- Booking history
- Booking cancellation
- Database persistence
"""
import sys
import os
import unittest
import json
from datetime import date, timedelta

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Use dedicated isolated test database
TEST_DB_PATH = os.path.join(BASE_DIR, 'test_fanclub.db')
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB_PATH}'
os.environ['FLASK_ENV'] = 'testing'

from app import app
from models import db, User, Venue, Booking, Team, TeamMember, Match
from werkzeug.security import check_password_hash

class FanClubFullTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

        with app.app_context():
            db.drop_all()
            db.create_all()
            from scripts.init_db import init_database
            init_database(verbose=False)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.drop_all()
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except Exception:
                pass


    def test_01_new_user_registration(self):
        """Test real server-side registration of a new user."""
        payload = {
            'name': 'Marcus Rashford',
            'email': 'rashford@manunited.local',
            'phone': '9812345678',
            'password': 'StrongPassword2026!'
        }
        res = self.client.post('/api/register', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('user_id', data)

        with app.app_context():
            user = User.query.filter_by(email='rashford@manunited.local').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'Marcus Rashford')
            self.assertEqual(user.role, 'user')

    def test_02_duplicate_email_rejection(self):
        """Test rejection of registration with duplicate email address."""
        payload = {
            'name': 'Duplicate User',
            'email': 'rashford@manunited.local',
            'phone': '9900112233',
            'password': 'AnotherPassword2026!'
        }
        res = self.client.post('/api/register', json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('already registered', data['message'].lower())

    def test_03_password_hashing(self):
        """Test that passwords are saved as secure cryptographic hashes and never plaintext."""
        with app.app_context():
            user = User.query.filter_by(email='rashford@manunited.local').first()
            self.assertIsNotNone(user)
            # Must not be equal to original password
            self.assertNotEqual(user.password_hash, 'StrongPassword2026!')
            # Must verify properly with check_password_hash
            self.assertTrue(check_password_hash(user.password_hash, 'StrongPassword2026!'))
            # Must start with standard secure hash identifier
            self.assertTrue(user.password_hash.startswith(('scrypt:', 'pbkdf2:sha256:')))

    def test_04_successful_login(self):
        """Test logging in with registered credentials."""
        res = self.client.post('/api/login', json={
            'email': 'rashford@manunited.local',
            'password': 'StrongPassword2026!'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], 'rashford@manunited.local')

        # Check /api/me session verification
        me_res = self.client.get('/api/me')
        self.assertEqual(me_res.status_code, 200)
        self.assertTrue(me_res.get_json()['authenticated'])

    def test_05_incorrect_password_rejection(self):
        """Test login rejection when password does not match."""
        res = self.client.post('/api/login', json={
            'email': 'rashford@manunited.local',
            'password': 'WrongPassword123'
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('invalid credentials', data['message'].lower())

    def test_06_logout(self):
        """Test logging out clears the active session."""
        # Ensure logged in first
        self.client.post('/api/login', json={
            'email': 'rashford@manunited.local',
            'password': 'StrongPassword2026!'
        })
        logout_res = self.client.get('/logout')
        self.assertEqual(logout_res.status_code, 302)

        # After logout, /api/me must return 401
        me_res = self.client.get('/api/me')
        self.assertEqual(me_res.status_code, 401)

    def test_07_unauthorized_access_prevention(self):
        """Test that unauthenticated requests to protected endpoints are rejected."""
        # Ensure session is empty
        self.client.get('/logout')

        # Protected pages must redirect to login
        res = self.client.get('/bookings')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

        res_prof = self.client.get('/profile')
        self.assertEqual(res_prof.status_code, 302)
        self.assertIn('/login', res_prof.headers.get('Location', ''))

    def test_08_administrator_access_control(self):
        """Test that regular users are blocked from admin portal and only admins have access."""
        # 1. Login as regular player
        self.client.post('/api/login', json={
            'email': 'rashford@manunited.local',
            'password': 'StrongPassword2026!'
        })
        unauth_stats = self.client.get('/api/stats')
        self.assertEqual(unauth_stats.status_code, 403)

        unauth_dash = self.client.get('/admin/dashboard')
        self.assertEqual(unauth_dash.status_code, 302)

        # 2. Create and provision an administrator
        from scripts.create_admin import create_or_promote_admin
        create_or_promote_admin('Head Official', 'official@fanclub.local', '9988776655', 'AdminMaster2026!')

        # 3. Login as administrator
        admin_login = self.client.post('/api/login', json={
            'email': 'official@fanclub.local',
            'password': 'AdminMaster2026!'
        })
        self.assertEqual(admin_login.status_code, 200)
        self.assertEqual(admin_login.get_json()['user']['role'], 'admin')

        # 4. Access admin stats
        stats_res = self.client.get('/api/stats')
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.get_json()['stats']
        self.assertGreaterEqual(stats['total_users'], 2)
        self.assertGreaterEqual(stats['total_venues'], 3)

    def test_09_successful_booking_creation(self):
        """Test successful pitch booking creation and database commitment."""
        with app.app_context():
            venue = Venue.query.filter_by(name='Ryan Vibgyor KPC Empyrean').first()
            self.assertIsNotNone(venue)
            venue_id = venue.id

        # Log in as Marcus Rashford so the booking is assigned to this user
        login_res = self.client.post('/api/login', json={
            'email': 'rashford@manunited.local',
            'password': 'StrongPassword2026!'
        })
        self.assertEqual(login_res.status_code, 200)

        target_date = (date.today() + timedelta(days=4)).strftime('%Y-%m-%d')
        target_slot = "8:00 PM – 9:00 PM"

        payload = {
            'venue_id': venue_id,
            'date': target_date,
            'time_slot': target_slot,
            'contact_name': 'Marcus Rashford',
            'contact_phone': '9812345678'
        }

        res = self.client.post('/bookings/create', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('FC-2026-', data['booking_code'])
        self.__class__.test_booking_id = data['booking_id']
        self.__class__.test_venue_id = venue_id
        self.__class__.test_date = target_date
        self.__class__.test_slot = target_slot

        # Verify voucher view
        voucher_res = self.client.get(f"/bookings/{data['booking_id']}")
        self.assertEqual(voucher_res.status_code, 200)
        self.assertIn(b'Booking Confirmation Voucher', voucher_res.data)

    def test_10_duplicate_slot_booking_prevention(self):
        """Test that booking the same venue, date, and slot is strictly rejected by the server."""
        payload = {
            'venue_id': self.__class__.test_venue_id,
            'date': self.__class__.test_date,
            'time_slot': self.__class__.test_slot,
            'contact_name': 'Another Striker',
            'contact_phone': '9900000000'
        }
        # Attempt second booking on the same slot
        dup_res = self.client.post('/bookings/create', json=payload)
        self.assertEqual(dup_res.status_code, 400)
        data = dup_res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('already been booked', data['message'].lower())

    def test_11_booking_history(self):
        """Test that user can view their booking history accurately."""
        # Login as Rashford
        self.client.post('/api/login', json={
            'email': 'rashford@manunited.local',
            'password': 'StrongPassword2026!'
        })
        res = self.client.get('/bookings')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Ryan Vibgyor KPC Empyrean', res.data)

    def test_12_booking_cancellation(self):
        """Test cancelling a booking and releasing the slot for others."""
        booking_id = self.__class__.test_booking_id
        cancel_res = self.client.post(f'/bookings/{booking_id}/cancel')
        self.assertEqual(cancel_res.status_code, 200)
        self.assertTrue(cancel_res.get_json()['success'])

        # Verify slot is re-opened in availability API
        slots_res = self.client.get(f"/api/venues/{self.__class__.test_venue_id}/slots?date={self.__class__.test_date}")
        slots_data = slots_res.get_json()
        slot_obj = next(s for s in slots_data['slots'] if s['time'] == self.__class__.test_slot)
        self.assertTrue(slot_obj['is_available'], "Slot must be available again after cancellation")

    def test_13_database_persistence(self):
        """Test that database records are persistent across queries."""
        with app.app_context():
            user = User.query.filter_by(email='rashford@manunited.local').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'Marcus Rashford')

            booking = db.session.get(Booking, self.__class__.test_booking_id)
            self.assertIsNotNone(booking)
            self.assertEqual(booking.status, 'Cancelled')

if __name__ == '__main__':
    unittest.main()
