from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

from models import db, User, Group, Task, Meeting, Evidence
from scoring import get_leaderboard, update_user_score, approve_evidence, reject_evidence

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rsd.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['INSTANCE_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Create upload folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    users = get_leaderboard()
    return render_template('index.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Đăng nhập thành công!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        group_id = request.form.get('group_id')
        
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại', 'error')
            return render_template('register.html', groups=Group.query.all())
        
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password, group_id=group_id)
        db.session.add(user)
        db.session.commit()
        
        flash('Đăng ký thành công! Vui lòng đăng nhập', 'success')
        return redirect(url_for('login'))
    
    groups = Group.query.all()
    return render_template('register.html', groups=groups)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất', 'success')
    return redirect(url_for('index'))

@app.route('/my-tasks')
@login_required
def my_tasks():
    tasks = Task.query.order_by(Task.deadline).all()
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
        evidence_type = request.form['evidence_type']
        description = request.form['description']
        task_id = request.form.get('task_id')
        meeting_id = request.form.get('meeting_id')
        
        task_id = int(task_id) if task_id else None
        meeting_id = int(meeting_id) if meeting_id else None
        
        # Handle file upload
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                filename = f"{current_user.id}_{datetime.now().timestamp()}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file_path = filename
        
        evidence = Evidence(
            user_id=current_user.id,
            task_id=task_id,
            meeting_id=meeting_id,
            description=description,
            file_path=file_path
        )
        db.session.add(evidence)
        db.session.commit()
        
        flash('Nộp minh chứng thành công!', 'success')
        return redirect(url_for('my_evidences'))
    
    tasks = Task.query.all()
    meetings = Meeting.query.all()
    return render_template('submit_evidence.html', tasks=tasks, meetings=meetings)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    return render_template('admin.html')

@app.route('/admin/tasks')
@login_required
def admin_tasks():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('admin_tasks.html', tasks=tasks)

@app.route('/admin/meetings')
@login_required
def admin_meetings():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    meetings = Meeting.query.order_by(Meeting.date.desc()).all()
    return render_template('admin_meetings.html', meetings=meetings)

@app.route('/admin/evidences')
@login_required
def admin_evidences():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    evidences = Evidence.query.filter_by(status='pending').order_by(Evidence.submitted_at.desc()).all()
    return render_template('admin_evidences.html', evidences=evidences)

@app.route('/admin/approve-evidence/<int:evidence_id>', methods=['POST'])
@login_required
def admin_approve_evidence(evidence_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    
    points = float(request.form.get('points', 0))
    if approve_evidence(evidence_id, points, current_user.id):
        flash('Duyệt minh chứng thành công!', 'success')
    else:
        flash('Không thể duyệt minh chứng', 'error')
    
    return redirect(url_for('admin_evidences'))

@app.route('/admin/reject-evidence/<int:evidence_id>', methods=['POST'])
@login_required
def admin_reject_evidence(evidence_id):
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    
    if reject_evidence(evidence_id, current_user.id):
        flash('Từ chối minh chứng', 'warning')
    else:
        flash('Không thể từ chối minh chứng', 'error')
    
    return redirect(url_for('admin_evidences'))

@app.route('/admin/create-task', methods=['GET', 'POST'])
@login_required
def create_task():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        points = float(request.form['points'])
        deadline = request.form.get('deadline')
        
        if deadline:
            deadline = datetime.strptime(deadline, '%Y-%m-%d')
        
        task = Task(title=title, description=description, points=points, deadline=deadline)
        db.session.add(task)
        db.session.commit()
        
        flash('Tạo task thành công!', 'success')
        return redirect(url_for('admin_tasks'))
    
    return render_template('create_task.html')

@app.route('/admin/create-meeting', methods=['GET', 'POST'])
@login_required
def create_meeting():
    if current_user.role != 'admin':
        flash('Bạn không có quyền truy cập', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        location = request.form.get('location')
        notes = request.form.get('notes')
        
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        
        meeting = Meeting(title=title, date=date, location=location, notes=notes)
        db.session.add(meeting)
        db.session.commit()
        
        flash('Tạo buổi họp thành công!', 'success')
        return redirect(url_for('admin_meetings'))
    
    return render_template('create_meeting.html')

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            
            # Create some sample groups
            group1 = Group(name='Nhóm 1')
            group2 = Group(name='Nhóm 2')
            db.session.add_all([group1, group2])
            
            db.session.commit()
            print("Database initialized with default admin (username: admin, password: admin123)")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
