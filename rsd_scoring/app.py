from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rsd-scoring-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/rsd.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, member
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    score = db.Column(db.Integer, default=0)
    violations_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    group = db.relationship('Group', backref='members')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic')
    evidences = db.relationship('Evidence', backref='submitter', lazy='dynamic')

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
class Meeting(db.Model):
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
    
    agenda_assignee = db.relationship('User', foreign_keys=[agenda_assigned_to])
    minutes_assignee = db.relationship('User', foreign_keys=[minutes_assigned_to])
    attendances = db.relationship('Attendance', backref='meeting', lazy='dynamic')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    status = db.Column(db.String(20), default='absent')  # present, absent_excused, absent_unexcused
    excuse_evidence = db.Column(db.Text)
    excuse_approved = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref='attendances')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, overdue
    completed_at = db.Column(db.DateTime)
    early_completion_bonus = db.Column(db.Boolean, default=False)
    
class Evidence(db.Model):
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
    
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    violation_type = db.Column(db.String(50), nullable=False)
    points_deducted = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='violations')

class BonusPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bonus_type = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='bonus_points')
    granter = db.relationship('User', foreign_keys=[granted_by])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== HELPER FUNCTIONS ====================

def update_user_score(user_id, points):
    user = User.query.get(user_id)
    if user:
        user.score += points
        if points < 0:
            user.violations_count += 1
        db.session.commit()

def check_consecutive_absences(user_id, meeting_type):
    """Check for consecutive absences and apply penalties"""
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

# ==================== ROUTES ====================

@app.route('/')
def index():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('index.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Đăng nhập thất bại. Kiểm tra lại username và password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        group_name = request.form.get('group_name')
        
        if User.query.filter_by(username=username).first():
            flash('Username đã tồn tại.', 'error')
            return render_template('register.html')
        
        # Find or create group
        group = Group.query.filter_by(name=group_name).first()
        if not group:
            group = Group(name=group_name)
            db.session.add(group)
            db.session.commit()
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            group_id=group.id,
            role='member'
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('login'))
    
    groups = Group.query.all()
    return render_template('register.html', groups=groups)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
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

@app.route('/admin/meetings')
@login_required
def admin_meetings():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('admin_meetings.html', meetings=meetings)

@app.route('/admin/meetings/create', methods=['GET', 'POST'])
@login_required
def create_meeting():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
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
        return redirect(url_for('admin_meetings'))
    
    users = User.query.filter_by(role='member').all()
    return render_template('create_meeting.html', users=users)

@app.route('/admin/attendance/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def manage_attendance(meeting_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
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
        return redirect(url_for('admin_meetings'))
    
    # Get existing attendances
    attendances = {a.user_id: a for a in Attendance.query.filter_by(meeting_id=meeting_id).all()}
    members = User.query.filter_by(role='member').all()
    
    return render_template('attendance.html', meeting=meeting, members=members, attendances=attendances)

@app.route('/admin/tasks')
@login_required
def admin_tasks():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
    tasks = Task.query.order_by(Task.deadline.desc()).all()
    return render_template('admin_tasks.html', tasks=tasks)

@app.route('/admin/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
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
        return redirect(url_for('admin_tasks'))
    
    users = User.query.filter_by(role='member').all()
    return render_template('create_task.html', users=users)

@app.route('/admin/evidences')
@login_required
def admin_evidences():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
    evidences = Evidence.query.filter_by(status='pending').order_by(Evidence.submitted_at.desc()).all()
    return render_template('admin_evidences.html', evidences=evidences)

@app.route('/admin/evidences/<int:evidence_id>/review', methods=['POST'])
@login_required
def review_evidence(evidence_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
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
    return redirect(url_for('admin_evidences'))

@app.route('/admin/bonus', methods=['GET', 'POST'])
@login_required
def admin_bonus():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
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
        return redirect(url_for('admin_bonus'))
    
    users = User.query.filter_by(role='member').all()
    bonuses = BonusPoint.query.order_by(BonusPoint.created_at.desc()).limit(20).all()
    
    return render_template('admin_bonus.html', users=users, bonuses=bonuses)

@app.route('/admin/violations')
@login_required
def admin_violations():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
    violations = Violation.query.order_by(Violation.created_at.desc()).all()
    users_with_violations = User.query.filter(User.violations_count > 0).order_by(User.violations_count.desc()).all()
    
    return render_template('admin_violations.html', violations=violations, users_with_violations=users_with_violations)

@app.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('index'))
    
    # BCN candidates: score >= 85, violations <= 3
    bcn_candidates = User.query.filter(
        User.score >= 85,
        User.violations_count <= 3
    ).order_by(User.score.desc()).all()
    
    all_users = User.query.order_by(User.score.desc()).all()
    
    return render_template('admin_reports.html', bcn_candidates=bcn_candidates, all_users=all_users)

@app.route('/my-tasks')
@login_required
def my_tasks():
    tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.deadline.desc()).all()
    return render_template('my_tasks.html', tasks=tasks)

@app.route('/my-evidences')
@login_required
def my_evidences():
    evidences = Evidence.query.filter_by(user_id=current_user.id).order_by(Evidence.submitted_at.desc()).all()
    return render_template('my_evidences.html', evidences=evidences)

@app.route('/submit-evidence', methods=['GET', 'POST'])
@login_required
def submit_evidence():
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
        return redirect(url_for('my_evidences'))
    
    return render_template('submit_evidence.html')

# ==================== INIT DATABASE ====================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                full_name='Administrator',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin account created: admin / admin123')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
