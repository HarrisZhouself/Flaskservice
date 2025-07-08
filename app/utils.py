import os
import re
import sqlite3
import logging
from datetime import timedelta
from flask import current_app
from .models import TranslateHistory, db  # 导入模型和db

logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def get_history_db():
    db_path = os.path.join(basedir, 'instance', 'translateHistory.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_lock_time_test_version(failed_attempts):
    """根据失败次数返回锁定时间（测试用简化版本）"""
    if failed_attempts == 5:
        return timedelta(minutes=2)
    elif failed_attempts >= 8:
        return timedelta(minutes=3)
    return None


def validate_password(password):
    """增强版密码复杂度验证"""
    # 检查空密码
    if not password or password.isspace():
        return False, "密码不能为空或纯空格"

    # 长度检查
    if len(password) < 8:
        return False, "密码长度至少8个字符"
    if len(password) > 16:
        return False, "密码长度最多16个字符"

    # 字符类型检查
    checks = [
        (r'[A-Z]', "密码必须包含至少一个大写字母"),
        (r'[a-z]', "密码必须包含至少一个小写字母"),
        (r'[0-9]', "密码必须包含至少一个数字"),
        (r'[!@#$%^&*(),.?":{}|<>]', "密码必须包含至少一个特殊字符"),
    ]

    for pattern, message in checks:
        if not re.search(pattern, password):
            return False, message

    # 禁止特定字符
    dangerous_chars_pattern = r'[\s\/\\\'"`;|<>¥\x00-\x1F\x7F\u0080-\uFFFF]'
    if re.search(dangerous_chars_pattern, password):
        return False, "密码包含危险字符（如空格/引号/斜杠等）"

    # 常见弱密码检查
    weak_passwords = ['password', '12345678', 'qwertyui', 'admin123']
    if password.lower() in weak_passwords:
        return False, "密码过于简单，请使用更复杂的密码"

    return True, "密码符合要求"


def validate_username(username):
    """用户名安全验证（白名单模式）"""
    username = username.strip()

    # 基础检查
    if not username:
        return False, "用户名不能为空"
    if len(username) < 4:
        return False, "用户名至少4个字符"
    if len(username) > 20:
        return False, "用户名最多20个字符"

    # 白名单：只允许字母、数字、下划线、连字符和点
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', username):
        return False, "用户名只能包含字母、数字、下划线(_)、连字符(-)和点(.)"

    # 禁止常见攻击字符（即使白名单已覆盖，二次确认）
    dangerous_pattern = r'[\s\/\\\'"`;|<>]'
    if re.search(dangerous_pattern, username):
        return False, "用户名包含危险字符"

    # 禁止连续特殊字符（如 `..` 或 `--`）
    if re.search(r'[-_.]{2,}', username):
        return False, "用户名不能包含连续的特殊字符"

    # 禁止以特殊字符开头/结尾
    if username.startswith(('-', '_', '.')) or username.endswith(('-', '_', '.')):
        return False, "用户名不能以特殊字符开头或结尾"

    return True, "用户名有效"

def get_word_definition(word):
    """查询单词的中文释义"""
    dictionary_db = os.path.join(basedir, 'instance', 'dictionary.db')  # 你的词典数据库路径
    try:
        conn = sqlite3.connect(dictionary_db)
        cursor = conn.cursor()
        # 假设你的词典表结构是 word 和 translation 字段
        cursor.execute("SELECT translation FROM dictionary WHERE word = ?", (word.lower(),))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.error("词典表不存在，请检查数据库结构")
        else:
            logger.error(f"查询词典时出错: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"查询词典时发生意外错误: {str(e)}")
        return None


def get_translation_history(user_id, limit=10):
    """获取用户的翻译历史记录"""
    try:
        history_records = TranslateHistory.query.filter_by(
            user_id=user_id
        ).order_by(
            TranslateHistory.time.desc()
        ).limit(limit).all()

        return [{
            'word': record.word,
            'translation': record.translation,
            'time': record.time.strftime('%Y-%m-%d %H:%M:%S')
        } for record in history_records]
    except Exception as e:
        logger.error(f"获取翻译历史失败: {str(e)}")
        return []

def init_history_db():
    try:
        db.create_all()  # 这会创建所有已定义的模型对应的表
        logger.info("历史记录数据库初始化完成")
        print("🛢️ 历史记录数据库初始化完成")
    except Exception as e:
        logger.error(f"初始化历史记录数据库失败: {str(e)}")

def init_db():
    with current_app.app_context():
        try:
            db.create_all()
            print("🛢️ 数据库初始化完成")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {str(e)}")
            raise
