from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import secrets
import re
import os
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', default=secrets.token_hex(32))

if not app.secret_key:
    raise RuntimeError("未设置FLASK_SECRET_KEY！")

# 配置数据库
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'instance')
db_path = os.path.join(db_dir, 'data.db')
os.makedirs(db_dir, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.Index('idx_username_active', 'username', 'is_active'),
    )

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)

    @property
    def password(self):
        raise AttributeError('password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)


def init_db():
    with app.app_context():
        try:
            db.create_all()
            print("🛢️ 数据库初始化完成")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {str(e)}")
            raise

init_db()

@app.teardown_request
def teardown_request(exception=None):
    if exception:
        db.session.rollback()
    db.session.remove()

def validate_password(password):
    """密码复杂度验证"""
    if len(password) < 8:
        return False, "密码长度至少8个字符"
    if not re.search(r'[A-Z]', password):
        return False, "密码必须包含至少一个大写字母"
    if not re.search(r'[a-z]', password):
        return False, "密码必须包含至少一个小写字母"
    if not re.search(r'[0-9]', password):
        return False, "密码必须包含至少一个数字"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "密码必须包含至少一个特殊字符"
    return True, "密码符合要求"


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        app.logger.info(f"Login attempt: {username}")

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('账户不存在', 'error')
            return redirect(url_for('login'))

        if not user.is_active:
            flash('账户未激活，请先激活账户', 'warning')
            return redirect(url_for('activate'))  # 重定向到激活页面

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            user.is_active = True

            return redirect(url_for('home'))
        else:
            flash('密码错误', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # 验证密码复杂度
        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('该用户名已被注册', 'error')
            return redirect(url_for('register'))

        try:
            new_user = User()
            new_user.username = username
            new_user.password = password  # 自动通过@property加密
            db.session.add(new_user)
            db.session.commit()

            # 建立会话
            session.clear()
            session['user_id'] = new_user.id
            session['username'] = username
            session.permanent = True

            flash('注册成功！请登录', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"注册失败: {str(e)}")
            flash('注册过程出错，请重试', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/activate', methods=['GET', 'POST'])
def activate():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('账户不存在', 'error')
            return redirect(url_for('activate'))

        # 修正字段名：user.password -> user.password_hash
        if not check_password_hash(user.password_hash, password):
            flash('密码错误', 'error')
            return redirect(url_for('activate'))

        try:
            user.is_active = True
            db.session.commit()

            # 手动设置会话
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True

            flash('账户已激活', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"激活失败: {str(e)}")
            flash('激活过程中出错', 'error')
            return redirect(url_for('activate'))

    return render_template('activate.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session['username'])


@app.route('/logout', methods=['GET', 'POST'])  # 同时支持GET和POST
def logout():
    """退出登录，保留账户"""
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        user.is_active = False
        db.session.commit()

    session.clear()
    flash('您已安全退出，在激活后可以重新登录', 'info')
    return redirect(url_for('login'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    app.logger.warning(f"用户 {session['username']} 删除了账户")
    if 'user_id' not in session:
        """注销用户，永久注销"""
        return redirect(url_for('login'))
    """从数据库删除用户资料"""
    user = User.query.get(session['user_id'])
    if user:
        db.session.delete(user)
        db.session.commit()

    session.clear()
    flash('您的信息已经清除完毕，感谢使用我们的服务', 'warning')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context=None, debug=True, use_reloader=False)