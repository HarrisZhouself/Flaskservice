import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_user():
    mock_user_success = MagicMock()
    mock_user_success.username = 'testUser_Login_unit'
    mock_user_success.password_hash = '2wsx#EDC'
    mock_user_success.id = 1
    mock_user_success.is_active = False
    mock_user_success.is_locked = False
    mock_user_success.failed_attempts = 0
    mock_user_success.locked_until = None
    mock_user_success.last_failed_time = None
    mock_user_success.verify_password.return_value = False

    return mock_user_success