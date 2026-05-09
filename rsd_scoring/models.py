from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, leader, member
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    score = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    members = db.relationship('User', backref='group', lazy=True)
    
    def __repr__(self):
        return f'<Group {self.name}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    points = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Task {self.title}>'

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Meeting {self.title}>'

class Evidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    points_awarded = db.Column(db.Float, default=0.0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    user = db.relationship('User', foreign_keys=[user_id], backref='evidences')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    task = db.relationship('Task', backref='evidences')
    meeting = db.relationship('Meeting', backref='evidences')
    
    def __repr__(self):
        return f'<Evidence {self.id}>'
