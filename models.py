from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Semester(db.Model):
    __tablename__ = 'semesters'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    schedules = db.relationship('Schedule', backref='semester', lazy=True)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rules = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    schedules = db.relationship('Schedule', backref='room', lazy=True)
    reservations = db.relationship('RoomReservation', backref='room', lazy=True)

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subject_code = db.Column(db.String(50), nullable=False)
    subject_description = db.Column(db.String(255), nullable=False)
    color = db.Column(db.String(7), default='#3498db')

class Instructor(db.Model):
    __tablename__ = 'instructors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    contact = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    schedules = db.relationship('Schedule', backref='instructor_obj', lazy=True)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    subject_code = db.Column(db.String(50), nullable=False)
    subject_description = db.Column(db.String(255), nullable=False)
    instructor = db.Column(db.String(100), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructors.id'), nullable=True)
    day = db.Column(db.Enum('Monday','Tuesday','Wednesday','Thursday','Friday'), nullable=False)
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RoomReservation(db.Model):
    __tablename__ = 'room_reservations'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semesters.id'), nullable=False)
    day = db.Column(db.Enum('Monday','Tuesday','Wednesday','Thursday','Friday'), nullable=False)
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EnrollmentSettings(db.Model):
    __tablename__ = 'enrollment_settings'
    id = db.Column(db.Integer, primary_key=True)
    school_email = db.Column(db.String(100), default='acsicollegeiloilo31@gmail.com')
    gcash_number = db.Column(db.String(20), default='09639859782')
    gcash_name = db.Column(db.String(100), default='Chewyll Simora')
    palawan_number = db.Column(db.String(20), default='09639859782')
    palawan_name = db.Column(db.String(100), default='Chewyll Simora')
    requirements = db.Column(db.Text)
    courses = db.Column(db.Text)
    payment_notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)