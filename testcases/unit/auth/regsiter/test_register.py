from unittest.mock import patch, MagicMock
import pytest
from werkzeug.security import generate_password_hash

from testcases.unit.auth.login.test_login import TEST_USERNAME

TEST_USERNAME = 'testUser_Register'
INVALID_TEST_USEER = "testUser_Register_valid"
TEST_PASSWORD = '2wsx#EDC'
INVALID_PASSWORD = '5421'
TEST_HASHED_PASSWORD = generate_password_hash(TEST_PASSWORD)


@pytest.fixture()
def mock_user(mock_user):
    mock_user.username = TEST_USERNAME
    #mock_user.verify_password.return_value = True
    return mock_user

@pytest.fixture()
def mock_db():
    with patch('app.db.session.add'),\
         patch('app.db.session.commit'), \
         patch('app.db.session.rollback'): \
        yield

def test_register_success(client,mock_user):
    """
    success test scene
    correct username and password
    :return:
    """
    #1. 模拟检查数据库返回none（表示用户名可用）
    with patch('app.models.User.query') as mock_query:
         #patch('werkzeug.security.check_password_hash', return_value=True) as mock_check:
        mock_query.filter_by.return_value.first.return_value = None

        response = client.post(
            '/auth/register', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )

        #验证响应内容
        assert response.status_code == 200
        assert '注册成功！请登录' in response.get_data(as_text=True)

        #验证数据库内容
        mock_query.filter_by.assert_called_with(username=TEST_USERNAME)

        with client.session_transaction() as sess:
            assert sess['username'] == TEST_USERNAME
            assert 'user_id' in sess

def test_register_exist_user(client):

    #模拟已存在的用户
    exist_mock_user = MagicMock()

    with patch('app.models.User.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = exist_mock_user

        response = client.post(
            '/auth/register', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert '该用户名已被注册' in response.get_data(as_text=True)

#用户名复杂性验证
def test_register_invalid_username(client):

    response = client.post(
        '/auth/register', data={'username': INVALID_TEST_USEER, 'password': TEST_PASSWORD},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert '用户名无效' in response.get_data(as_text=True)

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

#密码复杂性验证
def test_register_invalid_password(client):
    response = client.post(
        '/auth/register', data={'username': TEST_USERNAME, 'password': INVALID_PASSWORD},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert '密码无效，注册失败' in response.get_data(as_text=True)

    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_register_db_error(client,mock_db):
    with patch('app.models.User.query') as mock_query,\
         patch('app.db.session.commit',side_effect=Exception('DB Error')):

        mock_query.filter_by.return_value.first.return_value = None

        response = client.post(
            '/auth/register', data={'username': TEST_USERNAME, 'password': TEST_PASSWORD},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert '注册过程出错，请重试' in response.get_data(as_text=True)

        with client.session_transaction() as sess:
            assert 'user_id' not in sess
