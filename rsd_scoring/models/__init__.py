"""
Database Models for RSD Scoring Application
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and scoring"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='member', index=True)  # admin, member
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), index=True)
    score = db.Column(db.Integer, default=0, index=True)
    violations_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    group = db.relationship('Group', backref='members')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    evidences = db.relationship('Evidence', backref='submitter', lazy='dynamic', foreign_keys='Evidence.user_id')
    violations = db.relationship('Violation', backref='user', lazy='dynamic', foreign_keys='Violation.user_id')
    bonus_points = db.relationship('BonusPoint', backref='user', lazy='dynamic', foreign_keys='BonusPoint.user_id')
    
    def set_password(self, password):
        """Hash and set password"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Group(db.Model):
    """Group model for organizing users"""
    __tablename__ = 'group'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<Group {self.name}>'


class Meeting(db.Model):
    """Meeting model for tracking club and board meetings"""
    __tablename__ = 'meeting'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_type = db.Column(db.String(20), nullable=False, index=True)  # 'clb', 'ban'
    date = db.Column(db.DateTime, nullable=False, index=True)
    agenda_assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    minutes_assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    agenda_submitted = db.Column(db.Boolean, default=False)
    minutes_submitted = db.Column(db.Boolean, default=False)
    agenda_deadline = db.Column(db.DateTime)
    minutes_deadline = db.Column(db.DateTime)
    
    # Relationships
    agenda_assignee = db.relationship('User', foreign_keys=[agenda_assigned_to])
    minutes_assignee = db.relationship('User', foreign_keys=[minutes_assigned_to])
    attendances = db.relationship('Attendance', backref='meeting', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Meeting {self.title}>'


class Attendance(db.Model):
    """Attendance model for tracking meeting attendance"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='absent', index=True)  # present, absent_excused, absent_unexcused
    excuse_evidence = db.Column(db.Text)
    excuse_approved = db.Column(db.Boolean, default=False)
    
    # Relationship
    user = db.relationship('User', backref='attendances')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'meeting_id', name='unique_user_meeting'),
    )
    
    def __repr__(self):
        return f'<Attendance User:{self.user_id} Meeting:{self.meeting_id}>'


class Task(db.Model):
    """Task model for assigning and tracking tasks"""
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    deadline = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='pending', index=True)  # pending, completed, overdue
    completed_at = db.Column(db.DateTime)
    early_completion_bonus = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Task {self.title}>'


class Evidence(db.Model):
    """Evidence model for submitting proof of activities"""
    __tablename__ = 'evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    evidence_type = db.Column(db.String(30), nullable=False, index=True)  # absence, task, idea, initiative, agenda, minutes
    description = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    points = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Relationship
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<Evidence {self.evidence_type} by User:{self.user_id}>'


class Violation(db.Model):
    """Violation model for tracking rule violations"""
    __tablename__ = 'violation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    violation_type = db.Column(db.String(50), nullable=False)
    points_deducted = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Violation {self.violation_type} by User:{self.user_id}>'


class BonusPoint(db.Model):
    """BonusPoint model for tracking bonus points awarded"""
    __tablename__ = 'bonus_point'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    bonus_type = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    granter = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self):
        return f'<BonusPoint {self.bonus_type} for User:{self.user_id}>'
