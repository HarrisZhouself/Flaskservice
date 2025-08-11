import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def authenticated_user(client):
    """模拟已登录用户"""
    client.post('/login', data={'username': 'test', 'password': 'test'})
    return client

def test_delete_with_fixture(authenticated_user):
    response = authenticated_user.post('/delete_account')
    assert response.status_code == 302
    assert url_for('auth.login') in response.location