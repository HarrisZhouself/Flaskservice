from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import re
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'


# 模拟用户数据库
bashdir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(bashdir, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    def __repr__(self):
        return f'<User {self.username}'

with app.app_context():
    db.create_all()

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

        if check_password_hash(user.password, password):
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
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('该用户名已被注册', 'error')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))

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

        if not check_password_hash(user.password, password):
            flash('密码错误', 'error')
            return redirect(url_for('activate'))

        # 激活账户
        user.is_active = True
        db.session.commit()

        flash('账户已激活，请登录', 'success')
        return redirect(url_for('login'))

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
    flash('您已安全退出，可以随时登录', 'info')
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