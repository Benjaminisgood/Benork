from flask import render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from datetime import datetime
from . import main_bp
from models import db, Expense, Tag

@main_bp.route('/')
def index():
    # 未登录则跳转登录页
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    # 已登录：管理员跳转审核页面，普通用户跳转提交页面
    if current_user.is_admin:
        return redirect(url_for('admin.pending_requests'))
    else:
        return redirect(url_for('main.submit_request'))

@main_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_request():
    # 报销申请提交页面（需登录后访问）
    tags = Tag.query.all()  # 获取所有分类标签供选择
    if request.method == 'POST':
        amount_str = request.form.get('amount')
        purpose = request.form.get('purpose')
        date_str = request.form.get('date')
        tag_id = request.form.get('tag')
        # 简单校验
        if not amount_str or not purpose or not date_str or not tag_id:
            flash('All fields are required.', 'warning')
            return render_template('main/submit.html', tags=tags)
        try:
            amount = float(amount_str)
        except ValueError:
            flash('Amount must be a number.', 'danger')
            return render_template('main/submit.html', tags=tags)
        # 解析日期
        try:
            expense_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            flash('Invalid date format.', 'danger')
            return render_template('main/submit.html', tags=tags)
        tag = Tag.query.get(int(tag_id))
        if not tag:
            flash('Selected category not found.', 'danger')
            return render_template('main/submit.html', tags=tags)
        # 创建新的报销申请（状态默认为 pending）
        new_expense = Expense(amount=amount, purpose=purpose, date=expense_date,
                               user_id=current_user.id, tag_id=tag.id)
        db.session.add(new_expense)
        db.session.commit()
        flash('Expense request submitted successfully.', 'success')
        return redirect(url_for('main.my_requests'))
    # GET 请求渲染表单页面
    return render_template('main/submit.html', tags=tags)

@main_bp.route('/my_requests')
@login_required
def my_requests():
    # 查询当前用户的所有报销申请，按日期倒序
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('main/my_requests.html', expenses=expenses)