"""
Main routes for the RSD Scoring application.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import User

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Display the main leaderboard page."""
    users = User.query.order_by(User.score.desc()).all()
    return render_template('index.html', users=users)


@main_bp.route('/my-tasks')
@login_required
def my_tasks():
    """Display current user's tasks."""
    from app.models import Task
    tasks = Task.query.filter_by(assigned_to=current_user.id).order_by(Task.deadline.desc()).all()
    return render_template('my_tasks.html', tasks=tasks)


@main_bp.route('/my-evidences')
@login_required
def my_evidences():
    """Display current user's evidence submissions."""
    from app.models import Evidence
    evidences = Evidence.query.filter_by(user_id=current_user.id).order_by(Evidence.submitted_at.desc()).all()
    return render_template('my_evidences.html', evidences=evidences)


@main_bp.route('/submit-evidence', methods=['GET', 'POST'])
@login_required
def submit_evidence():
    """Handle evidence submission."""
    from flask import request, flash, redirect, url_for
    from app.models import db, Evidence
    
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
