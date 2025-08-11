import pytest
import datetime

from datetime import datetime, timezone
from app.utils import get_lock_time_test_version
from unittest.mock import patch, PropertyMock
from flask import get_flashed_messages
from werkzeug.security import generate_password_hash


TEST_USERNAME = 'testUser_Login_unit'
TEST_PASSWORD = '2wsx#EDC'
TEST_HASHED_PASSWORD = generate_password_hash(TEST_PASSWORD)

@pytest.fixture()
def mock_user(mock_user):
    mock_user.verify_password.return_value = True
    mock_user.is_active = True

    return mock_user

@pytest.fixture()
def mock_not_active_user(mock_user):
    mock_user.is_active = False

    return mock_user

@pytest.fixture()
def mock_not_active_attempts(mock_user):
    mock_user.failed_attempts = 0
    mock_user.locked_until = None
    mock_user.last_failed_time = None
    mock_user.is_active = True
    mock_user.verify_password.return_value = False

    return mock_user

def test_login_success_with_valid_credentials(client, mock_user):
    # 1.mock_user

    # 2. 替换依赖项
    with patch('app.models.User.query') as mock_query, \
            patch('werkzeug.security.check_password_hash', return_value=True) as mock_check, \
            patch('app.db.session.commit') as mock_commit,\
            patch('flask_wtf.csrf.validate_csrf', return_value=True),\
            patch('app.models.User.is_locked',new_callable=PropertyMock,return_value = False):
        # 配置查询链式调用
        mock_query.filter_by.return_value.first.return_value = mock_user

        # 3. 发起登录请求
        response = client.post(
            '/auth/login', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )

        # 4. 验证行为
        assert response.status_code == 200
        assert '欢迎' in response.get_data(as_text=True)
        assert '您已成功登录系统' in response.get_data(as_text=True)

        # 验证数据库查询
        mock_query.filter_by.assert_called_once_with(username=TEST_USERNAME)  # 注意去掉__eq
        mock_user.verify_password.assert_called_once_with(TEST_PASSWORD)
        mock_commit.assert_called_once()

        # 验证Session自动设置
        with client.session_transaction() as sess:
            assert sess['username'] == TEST_USERNAME
            assert sess['user_id'] == mock_user.id

def test_login_failed_when_user_not_exist(client,mock_user):
    with patch('app.models.User.query') as mock_query, \
         patch('flask_wtf.csrf.validate_csrf', return_value=True):

        mock_query.filter_by.return_value.first.return_value = None

        response = client.post(
            '/auth/login',
            data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )
        assert response.status_code == 200
        assert '账户不存在' in response.get_data(as_text=True)

        #verify flash message
        messages = get_flashed_messages()
        assert any('账户不存在' in msg for msg in messages)

        #verify database select
        mock_query.filter_by.assert_called_once_with(username=TEST_USERNAME)

def test_login_failed_when_not_active(client, mock_not_active_user):
    with patch('app.models.User.query') as mock_query, \
            patch('app.db.session.commit') as mock_commit, \
            patch('flask_wtf.csrf.validate_csrf', return_value=True), \
            patch('app.models.User.is_locked', new_callable=PropertyMock, return_value=False):

        # 设置mock用户行为
        #mock_not_active_user.verify_password.return_value = True  # 假设密码验证通过
        mock_query.filter_by.return_value.first.return_value = mock_not_active_user

        response = client.post(
            '/auth/login',
            data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )

        # 验证响应
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert '账户未激活，请先激活账户' in response_text
        assert '点击<a href="/auth/activate">此处</a>激活账户' in response_text

        # 验证行为
        mock_query.filter_by.assert_called_once_with(username=TEST_USERNAME)
        mock_commit.assert_not_called()

        with client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'username' not in sess

@pytest.mark.parametrize("initial_attempts, expected_message", [
    (0, "您还有 4 次尝试机会"),    # 第一次失败
    (3, "您还有 1 次尝试机会"),    # 临近锁定
    (4, "账户已被锁定2分钟"),      # 正好触发锁定
])
def test_login_failed_when_locks_account_less_5_attempts(client, mock_not_active_attempts,initial_attempts, expected_message):
    #1.特例化参数
    mock_not_active_attempts.failed_attempts = initial_attempts
    mock_not_active_attempts.last_failed_time = datetime.now(timezone.utc)
    mock_not_active_attempts.locked_until = datetime.now(timezone.utc) + get_lock_time_test_version(mock_not_active_attempts.failed_attempts)

    # 2. 替换依赖项
    with patch('app.models.User.query') as mock_query, \
            patch('werkzeug.security.check_password_hash', return_value=True) as mock_check, \
            patch('app.db.session.commit') as mock_commit,\
            patch('flask_wtf.csrf.validate_csrf', return_value=True),\
            patch('app.models.User.is_locked',new_callable=PropertyMock,return_value = False):
        # 配置查询链式调用
        mock_query.filter_by.return_value.first.return_value = mock_not_active_attempts

        # 3. 发起登录请求
        response = client.post(
            '/auth/login', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )

        # 4. 验证行为
        assert response.status_code == 200
        assert expected_message in response.get_data(as_text=True)
        assert mock_not_active_attempts.failed_attempts == initial_attempts + 1

        # 验证数据库查询
        mock_query.filter_by.assert_called_once_with(username=TEST_USERNAME)  # 注意去掉__eq
        mock_not_active_attempts.verify_password.assert_called_once_with(TEST_PASSWORD)
        mock_commit.assert_called_once()

        # 验证Session自动设置
        with client.session_transaction() as sess:
            assert 'username' not in sess  # ✅ 登录失败时 session 不应该有 username
            assert 'user_id' not in sess  # ✅ 登录失败时 session 不应该有 user_id

@pytest.mark.parametrize("initial_attempts, expected_message", [
    (5, "密码错误，您还有 2 次尝试机会，多次错误将锁定账户24小时"),    # 第一次失败
    (6, "密码错误，您还有 1 次尝试机会，多次错误将锁定账户24小时"),    # 临近锁定
    (7, "账户因多次失败已被锁定24小时"),      # 正好触发锁定
])
def test_login_failed_when_locks_account_after_5_failed_attempts(client, mock_not_active_attempts, initial_attempts, expected_message):
    #1.特例化参数
    mock_not_active_attempts.failed_attempts = initial_attempts

    mock_not_active_attempts.last_failed_time = datetime.now(timezone.utc)
    mock_not_active_attempts.locked_until = datetime.now(timezone.utc) + get_lock_time_test_version(mock_not_active_attempts.failed_attempts)

    # 2. 替换依赖项
    with patch('app.models.User.query') as mock_query, \
            patch('werkzeug.security.check_password_hash', return_value=True) as mock_check, \
            patch('app.db.session.commit') as mock_commit,\
            patch('flask_wtf.csrf.validate_csrf', return_value=True),\
            patch('app.models.User.is_locked',new_callable=PropertyMock,return_value = False):
        # 配置查询链式调用
        mock_query.filter_by.return_value.first.return_value = mock_not_active_attempts

        # 3. 发起登录请求
        response = client.post(
            '/auth/login', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )

        # 4. 验证行为
        assert response.status_code == 200
        assert expected_message in response.get_data(as_text=True)
        assert mock_not_active_attempts.failed_attempts == initial_attempts + 1

        # 验证数据库查询
        mock_query.filter_by.assert_called_once_with(username=TEST_USERNAME)  # 注意去掉__eq
        mock_not_active_attempts.verify_password.assert_called_once_with(TEST_PASSWORD)
        mock_commit.assert_called_once()

        # 验证Session自动设置
        with client.session_transaction() as sess:
            assert 'username' not in sess  # ✅ 登录失败时 session 不应该有 username
            assert 'user_id' not in sess  # ✅ 登录失败时 session 不应该有 user_id

