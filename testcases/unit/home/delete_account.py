import pytest
from unittest.mock import MagicMock, patch
from app.core.routes import delete_account
from flask import session, flash, url_for

from app.models import User


def test_delete_account_success():
    """测试成功删除账户的场景"""
    # 1. 模拟依赖项
    mock_user = MagicMock()
    mock_user.username = "test_user"

    with patch('your_app.db.session.get', return_value=mock_user) as mock_db_get, \
            patch('your_app.db.session.commit') as mock_commit, \
            patch('your_app.db.session.delete') as mock_delete, \
            patch('your_app.session', {'user_id': 123}), \
            patch('your_app.flash') as mock_flash, \
            patch('your_app.redirect') as mock_redirect:
        # 2. 调用被测函数
        result = delete_account()

        # 3. 验证行为
        mock_db_get.assert_called_once_with(User, 123)
        mock_delete.assert_called_once_with(mock_user)
        mock_commit.assert_called_once()
        mock_flash.assert_called_with('您的信息已经清除完毕，感谢使用我们的服务', 'warning')
        mock_redirect.assert_called_with(url_for('auth.login'))


def test_delete_account_no_session():
    """测试未登录时重定向到登录页"""
    with patch('your_app.session', {}), \
            patch('your_app.redirect') as mock_redirect:
        result = delete_account()
        mock_redirect.assert_called_with(url_for('auth.login'))