import pytest
from app import create_app, db
from app.models import User
from unittest.mock import MagicMock
@pytest.fixture
def mock_user():
    mock_user = MagicMock()
    mock_user.username = 'testUser_register'
    mock_user.password_hash = '3edc$RFV'
    mock_user.id = 1
    mock_user.is_active = False
    mock_user.is_locked = False
    mock_user.failed_attempts = 0
    mock_user.locked_until = None
    mock_user.last_failed_time = None
    mock_user.verify_password.return_value = False
    return mock_user

@pytest.fixture(scope='module')
def app():
    """创建测试应用实例"""
    app = create_app()

    # 测试专用配置
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """测试客户端"""
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_db(app):
    #自动清理测试数据库
    yield
    with app.app_context():
        # 清理测试用户
        User.query.filter(User.username.like("testUser_%")).delete()
        db.session.commit()
    print(f"\r\nclean up test user info")


def test_home_page(browser):
    #示例测试 - 访问首页
    browser.get("http://localhost:5000/home")
    assert "欢迎" in browser.title

@pytest.fixture
def test_client(app):
    """标记为测试专用的client"""
    return app.test_client()
