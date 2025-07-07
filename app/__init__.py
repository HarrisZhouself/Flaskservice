import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from .utils import init_db, init_history_db

load_dotenv()

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', default=secrets.token_hex(32))

    if not app.secret_key:
        raise RuntimeError("未设置FLASK_SECRET_KEY！")

    # 配置数据库
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_dir = os.path.join(basedir, '..', 'instance')
    db_path = os.path.join(db_dir, 'registerData.db')
    os.makedirs(db_dir, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    # 初始化扩展
    db.init_app(app)

    # 注册蓝图
    from .auth.routes import auth_bp
    from .translate.routes import translate_bp
    from .main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(translate_bp)
    app.register_blueprint(main_bp)

    # 初始化数据库
    with app.app_context():
        init_db()
        init_history_db()

    # 添加请求后处理
    @app.teardown_request
    def teardown_request(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()

    return app