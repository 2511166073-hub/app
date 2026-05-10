"""
Database Models for RSD Scoring Application

This module defines all database models used in the RSD Scoring application.
"""
from datetime import datetime
from typing import Optional, List, Any

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and scoring"""
    __tablename__ = 'user'
    
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash: str = db.Column(db.String(256), nullable=False)
    full_name: str = db.Column(db.String(120), nullable=False)
    role: str = db.Column(db.String(20), default='member', index=True)  # admin, member
    group_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('group.id'), index=True)
    score: int = db.Column(db.Integer, default=0, index=True)
    violations_count: int = db.Column(db.Integer, default=0)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    group = db.relationship('Group', backref='members')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    evidences = db.relationship('Evidence', backref='submitter', lazy='dynamic', foreign_keys='Evidence.user_id')
    violations = db.relationship('Violation', backref='user', lazy='dynamic', foreign_keys='Violation.user_id')
    bonus_points = db.relationship('BonusPoint', backref='user', lazy='dynamic', foreign_keys='BonusPoint.user_id')
    
    def set_password(self, password: str) -> None:
        """Hash and set password
        
        Args:
            password: Plain text password to hash and store
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password against hash
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches hash, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Group(db.Model):
    """Group model for organizing users"""
    __tablename__ = 'group'
    
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False, unique=True)
    
    def __repr__(self) -> str:
        return f'<Group {self.name}>'


class Meeting(db.Model):
    """Meeting model for tracking club and board meetings"""
    __tablename__ = 'meeting'
    
    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(200), nullable=False)
    meeting_type: str = db.Column(db.String(20), nullable=False, index=True)  # 'clb', 'ban'
    date: datetime = db.Column(db.DateTime, nullable=False, index=True)
    agenda_assigned_to: Optional[int] = db.Column(db.Integer, db.ForeignKey('user.id'))
    minutes_assigned_to: Optional[int] = db.Column(db.Integer, db.ForeignKey('user.id'))
    agenda_submitted: bool = db.Column(db.Boolean, default=False)
    minutes_submitted: bool = db.Column(db.Boolean, default=False)
    agenda_deadline: Optional[datetime] = db.Column(db.DateTime)
    minutes_deadline: Optional[datetime] = db.Column(db.DateTime)
    
    # Relationships
    agenda_assignee = db.relationship('User', foreign_keys=[agenda_assigned_to])
    minutes_assignee = db.relationship('User', foreign_keys=[minutes_assigned_to])
    attendances = db.relationship('Attendance', backref='meeting', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f'<Meeting {self.title}>'


class Attendance(db.Model):
    """Attendance model for tracking meeting attendance"""
    __tablename__ = 'attendance'
    
    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    meeting_id: int = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False, index=True)
    status: str = db.Column(db.String(20), default='absent', index=True)  # present, absent_excused, absent_unexcused
    excuse_evidence: Optional[str] = db.Column(db.Text)
    excuse_approved: bool = db.Column(db.Boolean, default=False)
    
    # Relationship
    user = db.relationship('User', backref='attendances')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'meeting_id', name='unique_user_meeting'),
    )
    
    def __repr__(self) -> str:
        return f'<Attendance User:{self.user_id} Meeting:{self.meeting_id}>'


class Task(db.Model):
    """Task model for assigning and tracking tasks"""
    __tablename__ = 'task'
    
    id: int = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(200), nullable=False)
    description: Optional[str] = db.Column(db.Text)
    assigned_to: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    deadline: datetime = db.Column(db.DateTime, nullable=False, index=True)
    status: str = db.Column(db.String(20), default='pending', index=True)  # pending, completed, overdue
    completed_at: Optional[datetime] = db.Column(db.DateTime)
    early_completion_bonus: bool = db.Column(db.Boolean, default=False)
    
    def __repr__(self) -> str:
        return f'<Task {self.title}>'


class Evidence(db.Model):
    """Evidence model for submitting proof of activities"""
    __tablename__ = 'evidence'
    
    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    evidence_type: str = db.Column(db.String(30), nullable=False, index=True)  # absence, task, idea, initiative, agenda, minutes
    description: str = db.Column(db.Text, nullable=False)
    file_url: Optional[str] = db.Column(db.String(500))
    status: str = db.Column(db.String(20), default='pending', index=True)  # pending, approved, rejected
    points: int = db.Column(db.Integer, default=0)
    submitted_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    reviewed_by: Optional[int] = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at: Optional[datetime] = db.Column(db.DateTime)
    review_notes: Optional[str] = db.Column(db.Text)
    
    # Relationship
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self) -> str:
        return f'<Evidence {self.evidence_type} by User:{self.user_id}>'


class Violation(db.Model):
    """Violation model for tracking rule violations"""
    __tablename__ = 'violation'
    
    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    violation_type: str = db.Column(db.String(50), nullable=False)
    points_deducted: int = db.Column(db.Integer, nullable=False)
    description: Optional[str] = db.Column(db.Text)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self) -> str:
        return f'<Violation {self.violation_type} by User:{self.user_id}>'


class BonusPoint(db.Model):
    """BonusPoint model for tracking bonus points awarded"""
    __tablename__ = 'bonus_point'
    
    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    bonus_type: str = db.Column(db.String(50), nullable=False)
    points: int = db.Column(db.Integer, nullable=False)
    description: Optional[str] = db.Column(db.Text)
    granted_by: Optional[int] = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    granter = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self) -> str:
        return f'<BonusPoint {self.bonus_type} for User:{self.user_id}>'
