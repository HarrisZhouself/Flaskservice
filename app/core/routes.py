from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, session, flash, request, abort
from ..models import User, db
from ..utils import get_translation_history, logger

core_bp  = Blueprint('core', __name__)


@core_bp.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('core.home'))
    return redirect(url_for('auth.login'))


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper


@core_bp.route('/home')
@login_required
def home():
    print(f"in home page")
    # 直接使用session中的用户名，避免重复验证
    return render_template('core/home.html',
                         username=session.get('username', 'Guest'),
                         word=request.args.get('word', ''),
                         definition=request.args.get('definition', ''),
                         history=get_translation_history(session['user_id']))


@core_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'user_id' not in session:
        abort(401)
    user = User.query.get(session['user_id'])
    if user:
        user.is_active = False
        db.session.commit()
        session.clear()  # 立即清除会话
        flash('已安全退出', 'success')

    session.clear()
    flash('您已安全退出，在激活后可以重新登录', 'info')
    return redirect(url_for('auth.login'))


@core_bp.route('/delete_account', methods=['POST'])
def delete_account():
    logger.warning(f"用户 {session['username']} 删除了账户")
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # 从数据库删除用户资料
    user = User.query.get(session['user_id'])
    if user:
        db.session.delete(user)
        db.session.commit()

    session.clear()
    flash('您的信息已经清除完毕，感谢使用我们的服务', 'warning')
    return redirect(url_for('auth.login'))

