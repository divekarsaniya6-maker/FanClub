"""
FanClub Platform - Database Models & Configuration
Supports both SQLite (local development) and PostgreSQL (production deployment).
"""
import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    memberships = db.relationship('TeamMember', backref='user', lazy=True, cascade='all, delete-orphan')

    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    sport = db.Column(db.String(50), default='Football', nullable=False)
    price_per_slot = db.Column(db.Float, default=200.0, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Float, default=4.9, nullable=False)
    facilities = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    bookings = db.relationship('Booking', backref='venue', lazy=True, cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='venue', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'sport': self.sport,
            'price_per_slot': self.price_per_slot,
            'image_url': self.image_url,
            'rating': self.rating,
            'facilities': self.facilities,
            'description': self.description,
            'is_active': self.is_active
        }

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False, index=True)
    venue_name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    booking_date = db.Column(db.String(10), nullable=False, index=True)  # YYYY-MM-DD
    time_slot = db.Column(db.String(50), nullable=False, index=True)     # e.g. "8:00 PM – 9:00 PM"
    amount = db.Column(db.Float, default=200.0, nullable=False)
    contact_name = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    payment_status = db.Column(db.String(50), default='Pending (Desk Settlement)', nullable=False)
    payment_method = db.Column(db.String(50), default='Pay at Venue', nullable=False)
    status = db.Column(db.String(30), default='Confirmed', nullable=False, index=True)  # 'Confirmed', 'Completed', 'Cancelled'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        db.Index('idx_slot_lookup', 'venue_id', 'booking_date', 'time_slot'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'booking_code': self.booking_code,
            'user_id': self.user_id,
            'venue_id': self.venue_id,
            'venue_name': self.venue_name,
            'location': self.location,
            'booking_date': self.booking_date,
            'time_slot': self.time_slot,
            'amount': self.amount,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    team_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    captain_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    captain_name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'team_code': self.team_code,
            'captain_id': self.captain_id,
            'captain_name': self.captain_name,
            'city': self.city,
            'description': self.description,
            'member_count': len(self.members)
        }

class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = db.Column(db.String(30), default='Player', nullable=False)  # 'Captain', 'Player'
    joined_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('team_id', 'user_id', name='uq_team_user'),
    )

class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='SET NULL'), nullable=True)
    match_date = db.Column(db.String(10), nullable=False, index=True)
    match_time = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), default='Scheduled', nullable=False)  # 'Scheduled', 'Completed', 'Cancelled'
    notes = db.Column(db.Text, nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    home_team = db.relationship('Team', foreign_keys=[home_team_id], backref='home_matches')
    away_team = db.relationship('Team', foreign_keys=[away_team_id], backref='away_matches')
