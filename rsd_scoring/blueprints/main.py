"""
Main Blueprint for RSD Scoring Application
Contains core routes for dashboard, meetings, tasks, and evidences
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Group, Meeting, Attendance, Task, Evidence, Violation, BonusPoint
from utils import (
    update_user_score, 
    check_consecutive_absences, 
    calculate_meeting_deadlines,
    get_bcn_candidates,
    parse_datetime
)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Display leaderboard of users sorted by score"""
    users = User.query.order_by(User.score.desc()).all()
    return render_template('index.html', users=users)


@main_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard with overview statistics"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
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


@main_bp.route('/admin/meetings')
@login_required
def admin_meetings():
    """List all meetings"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('admin_meetings.html', meetings=meetings)


@main_bp.route('/admin/meetings/create', methods=['GET', 'POST'])
@login_required
def create_meeting():
    """Create a new meeting"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        meeting_type = request.form.get('meeting_type')
        date_str = request.form.get('date')
        agenda_assigned_to = request.form.get('agenda_assigned_to')
        minutes_assigned_to = request.form.get('minutes_assigned_to')
        
        date = parse_datetime(date_str)
        agenda_deadline, minutes_deadline = calculate_meeting_deadlines(date)
        
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
        return redirect(url_for('main.admin_meetings'))
    
    users = User.query.filter_by(role='member').all()
    return render_template('create_meeting.html', users=users)


@main_bp.route('/admin/attendance/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def manage_attendance(meeting_id):
    """Manage attendance for a meeting"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
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
        return redirect(url_for('main.admin_meetings'))
    
    # Get existing attendances
    attendances = {a.user_id: a for a in Attendance.query.filter_by(meeting_id=meeting_id).all()}
    members = User.query.filter_by(role='member').all()
    
    return render_template('attendance.html', meeting=meeting, members=members, attendances=attendances)


@main_bp.route('/admin/tasks')
@login_required
def admin_tasks():
    """List all tasks"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    tasks = Task.query.order_by(Task.deadline.desc()).all()
    return render_template('admin_tasks.html', tasks=tasks)


@main_bp.route('/admin/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    """Create a new task"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        assigned_to = request.form.get('assigned_to')
        deadline_str = request.form.get('deadline')
        
        deadline = parse_datetime(deadline_str)
        
        task = Task(
            title=title,
            description=description,
            assigned_to=int(assigned_to),
            deadline=deadline
        )
        db.session.add(task)
        db.session.commit()
        
        flash('Tạo task thành công!', 'success')
        return redirect(url_for('main.admin_tasks'))
    
    users = User.query.filter_by(role='member').all()
    return render_template('create_task.html', users=users)


@main_bp.route('/admin/evidences')
@login_required
def admin_evidences():
    """List pending evidences for review"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    evidences = Evidence.query.filter_by(status='pending').order_by(Evidence.submitted_at.desc()).all()
    return render_template('admin_evidences.html', evidences=evidences)


@main_bp.route('/admin/evidences/<int:evidence_id>/review', methods=['POST'])
@login_required
def review_evidence(evidence_id):
    """Review and approve/reject evidence"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    evidence = Evidence.query.get_or_404(evidence_id)
    action = request.form.get('action')
    points = int(request.form.get('points', 0))
    notes = request.form.get('notes', '')
    
    evidence.status = 'approved' if action == 'approve' else 'rejected'
    evidence.points = points if action == 'approve' else 0
    evidence.reviewed_by = current_user.id
    evidence.reviewed_at = db.func.now()
    evidence.review_notes = notes
    
    if action == 'approve':
        update_user_score(evidence.user_id, points)
    
    db.session.commit()
    flash('Duyệt minh chứng thành công!', 'success')
    return redirect(url_for('main.admin_evidences'))


@main_bp.route('/admin/bonus', methods=['GET', 'POST'])
@login_required
def admin_bonus():
    """Grant bonus points to users"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
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
        return redirect(url_for('main.admin_bonus'))
    
    users = User.query.filter_by(role='member').all()
    bonuses = BonusPoint.query.order_by(BonusPoint.created_at.desc()).limit(20).all()
    
    return render_template('admin_bonus.html', users=users, bonuses=bonuses)


@main_bp.route('/admin/violations')
@login_required
def admin_violations():
    """View violations report"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    violations = Violation.query.order_by(Violation.created_at.desc()).all()
    users_with_violations = User.query.filter(User.violations_count > 0).order_by(User.violations_count.desc()).all()
    
    return render_template('admin_violations.html', violations=violations, users_with_violations=users_with_violations)


@main_bp.route('/admin/reports')
@login_required
def admin_reports():
    """Generate BCN candidate reports"""
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('main.index'))
    
    bcn_candidates = get_bcn_candidates()
    all_users = User.query.order_by(User.score.desc()).all()
    
    return render_template('admin_reports.html', bcn_candidates=bcn_candidates, all_users=all_users)


@main_bp.route('/my-tasks')
@login_required
def my_tasks():
    """View tasks assigned to current user"""
    tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.deadline.desc()).all()
    return render_template('my_tasks.html', tasks=tasks)


@main_bp.route('/my-evidences')
@login_required
def my_evidences():
    """View evidences submitted by current user"""
    evidences = Evidence.query.filter_by(user_id=current_user.id).order_by(Evidence.submitted_at.desc()).all()
    return render_template('my_evidences.html', evidences=evidences)


@main_bp.route('/submit-evidence', methods=['GET', 'POST'])
@login_required
def submit_evidence():
    """Submit new evidence"""
    if request.method == 'POST':
        evidence_type = request.form.get('evidence_type')
        description = request.form.get('description')
        file_url = request.form.get('file_url', '')
        
        evidence = Evidence(
            user_id=current_user.id,
            evidence_type=evidence_type,
            description=description,
            file_url=file_url
        )
        db.session.add(evidence)
        db.session.commit()
        
        flash('Nộp minh chứng thành công! Đang chờ duyệt.', 'success')
        return redirect(url_for('main.my_evidences'))
    
    return render_template('submit_evidence.html')
