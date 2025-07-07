from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date
from datetime import datetime

# 初始化数据库（在 app.py 中完成与 Flask app 的绑定）
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    # 关联到用户提交的所有报销申请
    expenses = db.relationship('Expense', backref='user', lazy=True)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    # 关联到该分类下的所有报销申请
    expenses = db.relationship('Expense', backref='tag', lazy=True)

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'
    # 外键关联
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)



class TutoringRecord(db.Model):
    __tablename__ = 'tutoring_records'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    content = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    teacher_feedback = db.Column(db.String(300), default='')
    student_feedback = db.Column(db.String(300), default='')
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'approved', 'rejected'

    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='tutoring_given')
    student = db.relationship('User', foreign_keys=[student_id], backref='tutoring_received')