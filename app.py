from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager
from auth import auth_bp
from main import main_bp
from admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库和登录管理
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 创建数据库表（如尚未创建）
with app.app_context():
    db.create_all()

# 注册各功能模块的 Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True)