from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from markupsafe import Markup

from ..models import User, db  # 从上级models导入
from ..utils import validate_password, get_lock_time_test_version, logger, validate_username # 从上级utils导入
from datetime import datetime
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    print(f"当前请求方法: {request.method}")
    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        logger.info(f"Login attempt: {username}")

        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"in not user")
            flash('账户不存在', 'error')
            return redirect(url_for('auth.login'))

        # 检查账户是否被锁定
        if user.is_locked:
            print(f"in user.is_locked")
            remaining_time = user.locked_until - datetime.utcnow()
            minutes = int(remaining_time.total_seconds() // 60)
            seconds = int(remaining_time.total_seconds() % 60)
            flash(f'账户已锁定，请 {minutes} 分 {seconds} 秒后再试', 'error')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            # 添加激活链接到flash消息
            flash('账户未激活，请先激活账户', 'warning')
            flash(Markup('点击<a href="{}">此处</a>激活账户').format(url_for('auth.activate')), 'info')
            return redirect(url_for('auth.login'))

        # 检查密码
        if user.verify_password(password):
            print(f"in check_password_hash")
            # 登录成功，重置失败计数
            user.failed_attempts = 0
            user.locked_until = None
            user.last_failed_time = None
            db.session.commit()

            session['user_id'] = user.id
            session['username'] = user.username
            session.modified = True
            user.is_active = True

            return redirect(url_for('core.home'))
        else:
            # 密码错误，增加失败计数
            user.failed_attempts += 1
            user.last_failed_time = datetime.utcnow()

            if user.failed_attempts < 5:
                remaining_attempts = 5 - user.failed_attempts
                flash(f'密码错误，您还有 {remaining_attempts} 次尝试机会', 'error')
            elif user.failed_attempts == 5:
                user.locked_until = datetime.utcnow() + get_lock_time_test_version(user.failed_attempts)
                flash('密码错误，账户已被锁定2分钟', 'error')
            elif 5 < user.failed_attempts < 8:
                remaining_attempts = 8 - user.failed_attempts
                flash(f'密码错误，您还有 {remaining_attempts} 次尝试机会，多次错误将锁定账户24小时', 'error')
            else:  # >= 8 次
                user.locked_until = datetime.utcnow() + get_lock_time_test_version(user.failed_attempts)
                flash('账户因多次失败已被锁定24小时', 'error')

            db.session.commit()
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 打印特定字段
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        is_username_valid, username_msg = validate_username(username)
        if not is_username_valid:
            flash(username_msg, 'error')
            flash('用户名无效，注册失败', 'error')
            return redirect(url_for('auth.register'))

        # 验证密码复杂度
        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'error')
            flash('密码无效，注册失败','error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('该用户名已被注册', 'error')
            return redirect(url_for('auth.register'))

        try:
            new_user = User()
            new_user.username = username
            new_user.password = password
            db.session.add(new_user)
            db.session.commit()

            # 建立会话
            session.clear()
            session['user_id'] = new_user.id
            session['username'] = username
            session.permanent = True

            flash('注册成功！请登录', 'success')
            print("注册成功，正在进入login页面")
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"注册失败: {str(e)}")
            flash('注册过程出错，请重试', 'error')
            return redirect(url_for('auth.register'))

    print("正在返回注册模板")
    return render_template('auth/register.html')

@auth_bp.route('/activate', methods=['GET', 'POST'])
def activate():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('账户不存在', 'error')
            return redirect(url_for('auth.activate'))

        if not check_password_hash(user.password_hash, password):
            flash('密码错误', 'error')
            return redirect(url_for('auth.activate'))

        try:
            user.is_active = True
            db.session.commit()
            flash('账户已激活，请登录', 'success')
            return redirect(url_for('auth.login'))  # 激活后跳转到登录页

        except Exception as e:
            db.session.rollback()
            logger.error(f"激活失败: {str(e)}")
            flash('激活过程中出错', 'error')
            return redirect(url_for('auth.activate'))

    # GET 请求时返回激活页面
    return render_template('auth/activate.html')  # 确保返回的是激活模板