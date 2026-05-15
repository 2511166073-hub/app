"""
Utility functions for the RSD Scoring application.
"""


def update_user_score(user_id, points):
    """Update a user's score by adding points.
    
    Args:
        user_id: The ID of the user to update
        points: The number of points to add (can be negative)
    """
    from app.models import db, User
    
    user = User.query.get(user_id)
    if user:
        user.score += points
        if points < 0:
            user.violations_count += 1
        db.session.commit()


def check_consecutive_absences(user_id, meeting_type):
    """Check for consecutive absences and apply penalties.
    
    Args:
        user_id: The ID of the user to check
        meeting_type: The type of meeting ('ban' or 'clb')
    """
    from flask import flash
    from app.models import User, Attendance, Meeting
    
    user = User.query.get(user_id)
    if not user:
        return
    
    # Get recent meetings of this type
    if meeting_type == 'ban':
        threshold = 2  # Vắng >2 buổi Ban
    else:
        threshold = 3  # Vắng >3 buổi CLB
    
    recent_absences = Attendance.query.filter_by(
        user_id=user_id,
        status='absent_unexcused'
    ).join(Meeting).filter(
        Meeting.meeting_type == meeting_type
    ).order_by(Meeting.date.desc()).limit(threshold + 1).all()
    
    if len(recent_absences) > threshold:
        flash(f'Cảnh báo: {user.full_name} vắng quá {threshold} buổi {meeting_type.upper()} liên tiếp!', 'warning')
