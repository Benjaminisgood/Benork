### 📄 tutoring/routes.py

from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import current_user, login_required
from datetime import datetime
from . import tutoring_bp
from models import db, User, TutoringRecord
import io
import pandas as pd
from flask import send_file

@tutoring_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_tutoring():
    users = User.query.all()
    if request.method == 'POST':
        date_str = request.form.get('date')
        content = request.form.get('content')
        student_id = request.form.get('student_id')
        teacher_id = request.form.get('teacher_id')

        if not date_str or not content or not student_id or not teacher_id:
            flash('All fields are required.', 'warning')
            return render_template('tutoring/submit.html', users=users)

        record = TutoringRecord(
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            content=content,
            teacher_id=int(teacher_id),
            student_id=int(student_id)
        )
        db.session.add(record)
        db.session.commit()
        flash('Tutoring record submitted.', 'success')
        return redirect(url_for('tutoring.my_tutoring'))

    return render_template('tutoring/submit.html', users=users)


@tutoring_bp.route('/my')
@login_required
def my_tutoring():
    records = TutoringRecord.query.filter((TutoringRecord.teacher_id == current_user.id) | (TutoringRecord.student_id == current_user.id)).all()
    return render_template('tutoring/my_records.html', records=records)


@tutoring_bp.route('/feedback/<int:record_id>', methods=['GET', 'POST'])
@login_required
def feedback(record_id):
    record = TutoringRecord.query.get_or_404(record_id)
    if current_user.id not in [record.teacher_id, record.student_id]:
        abort(403)
    if request.method == 'POST':
        if current_user.id == record.teacher_id:
            record.teacher_feedback = request.form.get('teacher_feedback')
        if current_user.id == record.student_id:
            record.student_feedback = request.form.get('student_feedback')
        db.session.commit()
        flash('Feedback submitted.', 'success')
        return redirect(url_for('tutoring.my_tutoring'))
    return render_template('tutoring/feedback.html', record=record)


@tutoring_bp.route('/admin/pending')
@login_required
def admin_pending():
    if not current_user.is_admin:
        abort(403)
    records = TutoringRecord.query.filter_by(status='pending').all()
    return render_template('tutoring/admin_pending.html', records=records)


@tutoring_bp.route('/admin/approve/<int:record_id>', methods=['POST'])
@login_required
def approve_record(record_id):
    if not current_user.is_admin:
        abort(403)
    record = TutoringRecord.query.get_or_404(record_id)
    record.status = 'approved'
    db.session.commit()
    flash('Record approved.', 'success')
    return redirect(url_for('tutoring.admin_pending'))


@tutoring_bp.route('/admin/reject/<int:record_id>', methods=['POST'])
@login_required
def reject_record(record_id):
    if not current_user.is_admin:
        abort(403)
    record = TutoringRecord.query.get_or_404(record_id)
    record.status = 'rejected'
    db.session.commit()
    flash('Record rejected.', 'info')
    return redirect(url_for('tutoring.admin_pending'))


@tutoring_bp.route('/export')
@login_required
def export_records():
    if not current_user.is_admin:
        abort(403)
    records = TutoringRecord.query.filter_by(status='approved').all()
    data = []
    for r in records:
        data.append({
            'Date': r.date.strftime('%Y-%m-%d'),
            'Teacher': r.teacher.username,
            'Student': r.student.username,
            'Content': r.content,
            'Teacher Feedback': r.teacher_feedback,
            'Student Feedback': r.student_feedback
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='tutoring_records.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



@tutoring_bp.route('/all')
@login_required
def all_tutoring():
    if not current_user.is_admin:
        abort(403)
    records = TutoringRecord.query.order_by(TutoringRecord.date.desc()).all()
    return render_template('tutoring/all_records.html', records=records)