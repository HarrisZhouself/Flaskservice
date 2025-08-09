from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from ..models import db
from ..models import TranslateHistory
from ..utils import get_word_definition
import logging

logger = logging.getLogger(__name__)
translate_bp = Blueprint('translate', __name__)


@translate_bp.route('/translate', methods=['POST'])
def translate_word():
    print("translating......")
    print("请求头:", request.headers)
    print("表单数据:", request.form)
    print("Cookies:", request.cookies)
    print("Session:", session)

    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('auth.login'))

    word = request.form.get('word', '').strip()
    if not word:
        flash('请输入要查询的单词', 'error')
        return redirect(url_for('core.translate_page'))

    try:
        definition = get_word_definition(word)

        if not definition:
            flash(f'未找到单词 "{word}" 的释义', 'warning')
            return redirect(url_for('core.translate_page'))

        # 保存到历史记录
        new_history = TranslateHistory(
            user_id=session['user_id'],
            word=word,
            translation=definition
        )
        db.session.add(new_history)
        db.session.commit()

        flash(f'"{word}" 的翻译已保存', 'success')
        return redirect(url_for('core.translate_page',
                                word=word,
                                definition=definition,
                                _anchor='translate-section'  # 滚动到翻译区域
                                ))

    except Exception as e:
        logger.error(f"翻译处理失败: {str(e)}", exc_info=True)
        flash('翻译处理过程中出现错误', 'error')
        return redirect(url_for('core.translate_page'))


@translate_bp.route('/clear_history', methods=['POST'])
def clear_history():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # 使用 auth.login

    try:
        # 使用 SQLAlchemy 删除历史记录
        TranslateHistory.query.filter_by(user_id=session['user_id']).delete()
        db.session.commit()
        flash('翻译历史已清除', 'success')
    except Exception as e:
        logger.error(f"清除历史记录失败: {str(e)}")
        flash('清除历史记录失败', 'error')

    # 使用新的端点引用
    return redirect(url_for('core.translate_page'))  # 使用 main.translate_page