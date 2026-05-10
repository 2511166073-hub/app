"""
Utility functions for RSD Scoring Application
"""
from datetime import datetime
from flask import flash
from models import db, User, Meeting, Attendance


def update_user_score(user_id, points):
    """
    Update user score and track violations if points are negative.
    
    Args:
        user_id: ID of the user to update
        points: Points to add (can be negative)
    """
    user = User.query.get(user_id)
    if user:
        user.score += points
        if points < 0:
            user.violations_count += 1
        db.session.commit()


def check_consecutive_absences(user_id, meeting_type):
    """
    Check for consecutive absences and apply penalties.
    
    Args:
        user_id: ID of the user to check
        meeting_type: Type of meeting ('clb' or 'ban')
    """
    user = User.query.get(user_id)
    if not user:
        return
    
    # Get recent meetings of this type
    threshold = 2 if meeting_type == 'ban' else 3
    
    recent_absences = Attendance.query.filter_by(
        user_id=user_id,
        status='absent_unexcused'
    ).join(Meeting).filter(
        Meeting.meeting_type == meeting_type
    ).order_by(Meeting.date.desc()).limit(threshold + 1).all()
    
    if len(recent_absences) > threshold:
        flash(f'Cảnh báo: {user.full_name} vắng quá {threshold} buổi {meeting_type.upper()} liên tiếp!', 'warning')


def calculate_meeting_deadlines(meeting_date):
    """
    Calculate agenda and minutes deadlines based on meeting date.
    
    Args:
        meeting_date: DateTime of the meeting
        
    Returns:
        Tuple of (agenda_deadline, minutes_deadline)
    """
    from datetime import timedelta
    
    # Agenda deadline: 22h trước 2 ngày
    agenda_deadline = meeting_date - timedelta(days=2, hours=2)
    # Minutes deadline: 22h cùng ngày
    minutes_deadline = meeting_date + timedelta(hours=22)
    
    return agenda_deadline, minutes_deadline


def get_bcn_candidates():
    """
    Get users who qualify as BCN candidates.
    
    Returns:
        List of users with score >= 85 and violations <= 3
    """
    return User.query.filter(
        User.score >= 85,
        User.violations_count <= 3
    ).order_by(User.score.desc()).all()


def parse_datetime(date_string):
    """
    Parse datetime string from form input.
    
    Args:
        date_string: String in format '%Y-%m-%dT%H:%M'
        
    Returns:
        datetime object
    """
    return datetime.strptime(date_string, '%Y-%m-%dT%H:%M')
