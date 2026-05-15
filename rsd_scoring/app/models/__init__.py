"""
Database models for the RSD Scoring application.
"""
from datetime import datetime
from flask_login import UserMixin

# Import db from factory to ensure single instance
from app.factory import db


class User(UserMixin, db.Model):
    """User model for authentication and scoring."""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, member
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    score = db.Column(db.Integer, default=0)
    violations_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    group = db.relationship('Group', backref='members')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    evidences = db.relationship('Evidence', backref='submitter', lazy='dynamic', foreign_keys='Evidence.user_id')
    attendances = db.relationship('Attendance', backref='user')
    violations = db.relationship('Violation', backref='user')
    bonus_points = db.relationship('BonusPoint', foreign_keys='BonusPoint.user_id', backref='user')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Group(db.Model):
    """Group model for organizing users."""
    __tablename__ = 'group'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Group {self.name}>'


class Meeting(db.Model):
    """Meeting model for tracking club and board meetings."""
    __tablename__ = 'meeting'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_type = db.Column(db.String(20), nullable=False)  # 'clb', 'ban'
    date = db.Column(db.DateTime, nullable=False)
    agenda_assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    minutes_assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    agenda_submitted = db.Column(db.Boolean, default=False)
    minutes_submitted = db.Column(db.Boolean, default=False)
    agenda_deadline = db.Column(db.DateTime)
    minutes_deadline = db.Column(db.DateTime)
    
    # Relationships
    agenda_assignee = db.relationship('User', foreign_keys=[agenda_assigned_to])
    minutes_assignee = db.relationship('User', foreign_keys=[minutes_assigned_to])
    attendances = db.relationship('Attendance', backref='meeting', lazy='dynamic')
    
    def __repr__(self):
        return f'<Meeting {self.title}>'


class Attendance(db.Model):
    """Attendance model for tracking meeting attendance."""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    status = db.Column(db.String(20), default='absent')  # present, absent_excused, absent_unexcused
    excuse_evidence = db.Column(db.Text)
    excuse_approved = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Attendance User:{self.user_id} Meeting:{self.meeting_id}>'


class Task(db.Model):
    """Task model for assigning and tracking tasks."""
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, overdue
    completed_at = db.Column(db.DateTime)
    early_completion_bonus = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Task {self.title}>'


class Evidence(db.Model):
    """Evidence model for submitting proof of activities."""
    __tablename__ = 'evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    evidence_type = db.Column(db.String(30), nullable=False)  # absence, task, idea, initiative, agenda, minutes
    description = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    points = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<Evidence {self.evidence_type} - User:{self.user_id}>'


class Violation(db.Model):
    """Violation model for tracking rule violations."""
    __tablename__ = 'violation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    violation_type = db.Column(db.String(50), nullable=False)
    points_deducted = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Violation {self.violation_type} - User:{self.user_id}>'


class BonusPoint(db.Model):
    """Bonus point model for granting extra points."""
    __tablename__ = 'bonus_point'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bonus_type = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    granter = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self):
        return f'<BonusPoint {self.bonus_type} - User:{self.user_id}>'
