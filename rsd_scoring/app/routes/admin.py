"""
Admin routes for the RSD Scoring application.
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db, User, Meeting, Attendance, Task, Evidence, BonusPoint, Violation, Group

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to restrict access to admin users only."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Bạn không có quyền truy cập trang này.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    """Display admin dashboard with statistics."""
    total_users = User.query.count()
    total_meetings = Meeting.query.count()
    total_tasks = Task.query.count()
    pending_evidences = Evidence.query.filter_by(status='pending').count()
    
    recent_meetings = Meeting.query.order_by(Meeting.date.desc()).limit(5).all()
    pending_tasks = Task.query.filter_by(status='pending').order_by(Task.deadline).limit(5).all()
    pending_evidences_list = Evidence.query.filter_by(status='pending').limit(5).all()
    
    return render_template('admin.html', 
                         total_users=total_users,
                         total_meetings=total_meetings,
                         total_tasks=total_tasks,
                         pending_evidences=pending_evidences,
                         recent_meetings=recent_meetings,
                         pending_tasks=pending_tasks,
                         pending_evidences_list=pending_evidences_list)


@admin_bp.route('/admin/meetings')
@login_required
@admin_required
def meetings():
    """Display all meetings."""
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('admin_meetings.html', meetings=meetings)


@admin_bp.route('/admin/meetings/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_meeting():
    """Create a new meeting."""
    if request.method == 'POST':
        title = request.form.get('title')
        meeting_type = request.form.get('meeting_type')
        date_str = request.form.get('date')
        agenda_assigned_to = request.form.get('agenda_assigned_to')
        minutes_assigned_to = request.form.get('minutes_assigned_to')
        
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        agenda_deadline = date - timedelta(days=2, hours=2)  # 22h trước 2 ngày
        minutes_deadline = date + timedelta(hours=22)  # 22h cùng ngày
        
        meeting = Meeting(
            title=title,
            meeting_type=meeting_type,
            date=date,
            agenda_assigned_to=int(agenda_assigned_to) if agenda_assigned_to else None,
            minutes_assigned_to=int(minutes_assigned_to) if minutes_assigned_to else None,
            agenda_deadline=agenda_deadline,
            minutes_deadline=minutes_deadline
        )
        db.session.add(meeting)
        db.session.commit()
        
        flash('Tạo buổi họp thành công!', 'success')
        return redirect(url_for('admin.meetings'))
    
    users = User.query.filter_by(role='member').all()
    return render_template('create_meeting.html', users=users)


@admin_bp.route('/admin/attendance/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_attendance(meeting_id):
    """Manage attendance for a meeting."""
    meeting = Meeting.query.get_or_404(meeting_id)
    
    if request.method == 'POST':
        for user in User.query.filter_by(role='member').all():
            status = request.form.get(f'status_{user.id}')
            excuse = request.form.get(f'excuse_{user.id}', '')
            
            attendance = Attendance.query.filter_by(
                user_id=user.id,
                meeting_id=meeting_id
            ).first()
            
            if not attendance:
                attendance = Attendance(user_id=user.id, meeting_id=meeting_id)
                db.session.add(attendance)
            
            attendance.status = status
            if status == 'absent_excused' and excuse:
                attendance.excuse_evidence = excuse
                attendance.excuse_approved = True
            
            # Apply penalties
            if status == 'absent_unexcused':
                if meeting.meeting_type == 'clb':
                    update_user_score(user.id, -2)
                else:
                    update_user_score(user.id, -1)
                check_consecutive_absences(user.id, meeting.meeting_type)
            elif status == 'absent_excused':
                if meeting.meeting_type == 'clb':
                    update_user_score(user.id, -1)
                # Ban meeting với phép không trừ điểm
        
        db.session.commit()
        flash('Điểm danh thành công!', 'success')
        return redirect(url_for('admin.meetings'))
    
    # Get existing attendances
    attendances = {a.user_id: a for a in Attendance.query.filter_by(meeting_id=meeting_id).all()}
    members = User.query.filter_by(role='member').all()
    
    return render_template('attendance.html', meeting=meeting, members=members, attendances=attendances)


@admin_bp.route('/admin/tasks')
@login_required
@admin_required
def tasks():
    """Display all tasks."""
    tasks = Task.query.order_by(Task.deadline.desc()).all()
    return render_template('admin_tasks.html', tasks=tasks)


@admin_bp.route('/admin/tasks/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_task():
    """Create a new task."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        assigned_to = request.form.get('assigned_to')
        deadline_str = request.form.get('deadline')
        
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        
        task = Task(
            title=title,
            description=description,
            assigned_to=int(assigned_to),
            deadline=deadline
        )
        db.session.add(task)
        db.session.commit()
        
        flash('Tạo task thành công!', 'success')
        return redirect(url_for('admin.tasks'))
    
    users = User.query.filter_by(role='member').all()
    return render_template('create_task.html', users=users)


@admin_bp.route('/admin/evidences')
@login_required
@admin_required
def evidences():
    """Display pending evidence submissions."""
    evidences = Evidence.query.filter_by(status='pending').order_by(Evidence.submitted_at.desc()).all()
    return render_template('admin_evidences.html', evidences=evidences)


@admin_bp.route('/admin/evidences/<int:evidence_id>/review', methods=['POST'])
@login_required
@admin_required
def review_evidence(evidence_id):
    """Review an evidence submission."""
    evidence = Evidence.query.get_or_404(evidence_id)
    action = request.form.get('action')
    points = int(request.form.get('points', 0))
    notes = request.form.get('notes', '')
    
    evidence.status = 'approved' if action == 'approve' else 'rejected'
    evidence.points = points if action == 'approve' else 0
    evidence.reviewed_by = current_user.id
    evidence.reviewed_at = datetime.utcnow()
    evidence.review_notes = notes
    
    if action == 'approve':
        update_user_score(evidence.user_id, points)
    
    db.session.commit()
    flash('Duyệt minh chứng thành công!', 'success')
    return redirect(url_for('admin.evidences'))


@admin_bp.route('/admin/bonus', methods=['GET', 'POST'])
@login_required
@admin_required
def bonus():
    """Grant bonus points."""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        bonus_type = request.form.get('bonus_type')
        points = int(request.form.get('points'))
        description = request.form.get('description')
        
        bonus = BonusPoint(
            user_id=int(user_id),
            bonus_type=bonus_type,
            points=points,
            description=description,
            granted_by=current_user.id
        )
        db.session.add(bonus)
        
        update_user_score(int(user_id), points)
        db.session.commit()
        
        flash('Cộng điểm thưởng thành công!', 'success')
        return redirect(url_for('admin.bonus'))
    
    users = User.query.filter_by(role='member').all()
    bonuses = BonusPoint.query.order_by(BonusPoint.created_at.desc()).limit(20).all()
    
    return render_template('admin_bonus.html', users=users, bonuses=bonuses)


@admin_bp.route('/admin/violations')
@login_required
@admin_required
def violations():
    """Display violations."""
    violations = Violation.query.order_by(Violation.created_at.desc()).all()
    users_with_violations = User.query.filter(User.violations_count > 0).order_by(User.violations_count.desc()).all()
    
    return render_template('admin_violations.html', violations=violations, users_with_violations=users_with_violations)


@admin_bp.route('/admin/reports')
@login_required
@admin_required
def reports():
    """Generate reports."""
    # BCN candidates: score >= 85, violations <= 3
    bcn_candidates = User.query.filter(
        User.score >= 85,
        User.violations_count <= 3
    ).order_by(User.score.desc()).all()
    
    all_users = User.query.order_by(User.score.desc()).all()
    
    return render_template('admin_reports.html', bcn_candidates=bcn_candidates, all_users=all_users)


# ==================== HELPER FUNCTIONS ====================

def update_user_score(user_id, points):
    """Update a user's score."""
    user = User.query.get(user_id)
    if user:
        user.score += points
        if points < 0:
            user.violations_count += 1
        db.session.commit()


def check_consecutive_absences(user_id, meeting_type):
    """Check for consecutive absences and apply penalties."""
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
