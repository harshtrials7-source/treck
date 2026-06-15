from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) # In production, use hashing (e.g., Werkzeug)
    role = db.Column(db.String(20), nullable=False)       # 'admin', 'staff', 'user'
    name = db.Column(db.String(100), nullable=False)
    contact_details = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'blacklisted', 'active'
    
    # Relationships
    assigned_treks = db.relationship('Trek', backref='staff_member', lazy=True)
    bookings = db.relationship('Booking', backref='trekker', lazy=True)

class Trek(db.Model):
    __tablename__ = 'treks'
    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False) # 'Easy', 'Moderate', 'Hard'
    duration = db.Column(db.Integer, nullable=False)      # In Days
    available_slots = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Open', 'Closed', 'Completed'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Relationships
    bookings = db.relationship('Booking', backref='trek_event', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Booked')   # 'Booked', 'Cancelled', 'Completed'