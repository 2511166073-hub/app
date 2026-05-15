"""
Authentication routes for the RSD Scoring application.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import db, User, Group

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Đăng nhập thất bại. Kiểm tra lại username và password.', 'error')
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
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
        return redirect(url_for('auth.login'))
    
    groups = Group.query.all()
    return render_template('register.html', groups=groups)


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('main.index'))
