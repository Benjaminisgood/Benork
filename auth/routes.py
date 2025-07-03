from flask import render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import auth_bp
from models import db, User

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # 如果用户已登录，直接重定向
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.pending_requests'))
        else:
            return redirect(url_for('main.submit_request'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'warning')
            return render_template('auth/register.html')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken, please choose another.', 'danger')
            return render_template('auth/register.html')
        # 创建新用户
        new_user = User(username=username, password_hash=generate_password_hash(password))
        # 如果是第一个用户，赋予管理员权限
        if User.query.first() is None:
            new_user.is_admin = True
        db.session.add(new_user)
        db.session.commit()
        # 自动登录新注册用户
        login_user(new_user)
        flash('Registration successful. Welcome!', 'success')
        # 根据角色跳转：管理员跳转管理员页面，普通用户跳转提交页面
        if new_user.is_admin:
            return redirect(url_for('admin.pending_requests'))
        else:
            return redirect(url_for('main.submit_request'))
    # GET 请求渲染注册页面
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # 已登录则跳转相应页面
        if current_user.is_admin:
            return redirect(url_for('admin.pending_requests'))
        else:
            return redirect(url_for('main.submit_request'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            # 如果是被强制跳转登录的，处理 next 参数
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            # 否则根据角色跳转
            if user.is_admin:
                return redirect(url_for('admin.pending_requests'))
            else:
                return redirect(url_for('main.submit_request'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))