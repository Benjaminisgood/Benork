from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import current_user, login_required
from . import admin_bp
from models import db, User, Expense, Tag
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, os, time

@admin_bp.before_request
def admin_required():
    # 管理员权限校验：未登录或非管理员则禁止访问
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if not current_user.is_admin:
        flash('Admin access is required to view this page.', 'danger')
        return redirect(url_for('main.index'))

@admin_bp.route('/')
@login_required
def admin_index():
    # 管理员首页默认跳转到待审核列表
    return redirect(url_for('admin.pending_requests'))

@admin_bp.route('/pending')
@login_required
def pending_requests():
    # 获取所有待审核的报销申请
    pending_list = Expense.query.filter_by(status='pending').order_by(Expense.date.desc()).all()
    return render_template('admin/pending.html', expenses=pending_list)

@admin_bp.route('/approve/<int:expense_id>', methods=['POST'])
@login_required
def approve_request(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.status != 'pending':
        flash('Expense request is not pending.', 'warning')
        return redirect(url_for('admin.pending_requests'))
    tag = expense.tag  # 通过 backref 获取关联的 Tag 对象
    # 计算该分类已批准的总开销
    current_spent = sum(e.amount for e in tag.expenses if e.status == 'approved')
    if current_spent + expense.amount > tag.budget:
        flash(f'Cannot approve: approving this would exceed budget for category "{tag.name}".', 'danger')
        return redirect(url_for('admin.pending_requests'))
    # 更新状态为已批准
    expense.status = 'approved'
    db.session.commit()
    flash('Expense request approved and added to the ledger.', 'success')
    return redirect(url_for('admin.pending_requests'))

@admin_bp.route('/reject/<int:expense_id>', methods=['POST'])
@login_required
def reject_request(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.status != 'pending':
        flash('Expense request is not pending.', 'warning')
        return redirect(url_for('admin.pending_requests'))
    # 更新状态为已拒绝
    expense.status = 'rejected'
    db.session.commit()
    flash('Expense request has been rejected.', 'info')
    return redirect(url_for('admin.pending_requests'))

@admin_bp.route('/tags')
@login_required
def manage_tags():
    tags = Tag.query.all()
    total_budget = 0
    total_spent = 0
    # 计算每个分类已用金额
    for tag in tags:
        spent = sum(e.amount for e in tag.expenses if e.status == 'approved')
        tag.current_usage = spent
        total_budget += tag.budget
        total_spent += spent
    total_remaining = total_budget - total_spent
    return render_template('admin/tags.html', tags=tags, total_budget=total_budget,
                           total_spent=total_spent, total_remaining=total_remaining)

@admin_bp.route('/tags/add', methods=['POST'])
@login_required
def add_tag():
    name = request.form.get('name')
    budget_str = request.form.get('budget')
    if not name or not budget_str:
        flash('Name and budget are required for new category.', 'warning')
        return redirect(url_for('admin.manage_tags'))
    try:
        budget_val = float(budget_str)
    except ValueError:
        flash('Budget must be a number.', 'danger')
        return redirect(url_for('admin.manage_tags'))
    # 检查名称是否已存在
    existing = Tag.query.filter_by(name=name).first()
    if existing:
        flash('Category name already exists.', 'danger')
        return redirect(url_for('admin.manage_tags'))
    new_tag = Tag(name=name, budget=budget_val)
    db.session.add(new_tag)
    db.session.commit()
    flash(f'Category "{name}" added.', 'success')
    return redirect(url_for('admin.manage_tags'))

@admin_bp.route('/tags/<int:tag_id>/update', methods=['POST'])
@login_required
def update_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    budget_str = request.form.get('budget')
    if not budget_str:
        flash('Budget value is required.', 'warning')
        return redirect(url_for('admin.manage_tags'))
    try:
        new_budget = float(budget_str)
    except ValueError:
        flash('Budget must be a number.', 'danger')
        return redirect(url_for('admin.manage_tags'))
    tag.budget = new_budget
    db.session.commit()
    flash(f'Budget for "{tag.name}" updated to {new_budget}.', 'success')
    return redirect(url_for('admin.manage_tags'))

@admin_bp.route('/stats')
@login_required
def stats():
    tags = Tag.query.all()
    chart_url = None
    if tags:
        data = []
        for tag in tags:
            spent = sum(e.amount for e in tag.expenses if e.status == 'approved')
            data.append({'Tag': tag.name, 'Spent': spent, 'Budget': tag.budget})
        df = pd.DataFrame(data).set_index('Tag')
        if not df.empty:
            # 绘制每个分类的支出 vs 预算柱状图
            fig, ax = plt.subplots(figsize=(6,4))
            df.plot(kind='bar', ax=ax)
            plt.title('Spending by Category')
            plt.ylabel('Amount')
            plt.tight_layout()
            # 保存图表到静态文件
            chart_path = os.path.join(os.getcwd(), 'static', 'stats.png')
            fig.savefig(chart_path)
            plt.close(fig)
            # 为避免浏览器缓存，加时间戳参数
            chart_url = url_for('static', filename='stats.png') + '?v=' + str(int(time.time()))
    total_spent = sum(e.amount for e in Expense.query.filter_by(status='approved').all())
    total_budget = sum(tag.budget for tag in tags)
    return render_template('admin/stats.html', chart_url=chart_url, total_spent=total_spent, total_budget=total_budget)

@admin_bp.route('/export/csv')
@login_required
def export_csv():
    # 导出所有已批准的报销记录为 CSV
    expenses = Expense.query.filter_by(status='approved').all()
    data = []
    for e in expenses:
        data.append({
            'ID': e.id,
            'User': e.user.username,
            'Category': e.tag.name,
            'Amount': e.amount,
            'Purpose': e.purpose,
            'Date': e.date.strftime('%Y-%m-%d')
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='expenses.csv', mimetype='text/csv')

@admin_bp.route('/export/excel')
@login_required
def export_excel():
    # 导出所有已批准的报销记录为 Excel
    expenses = Expense.query.filter_by(status='approved').all()
    data = []
    for e in expenses:
        data.append({
            'ID': e.id,
            'User': e.user.username,
            'Category': e.tag.name,
            'Amount': e.amount,
            'Purpose': e.purpose,
            'Date': e.date.strftime('%Y-%m-%d')
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='expenses.xlsx',
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')