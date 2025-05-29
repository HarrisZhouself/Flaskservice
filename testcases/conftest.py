import pytest
from app import db, User
from app import app as flask_app
from werkzeug.security import generate_password_hash
from selenium import webdriver

@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    yield flask_app


@pytest.fixture
def client(app):
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture(scope="module")
def bowser():
    driver = webdriver.Edge()
    yield driver
    driver.quit()

def test_home_page(bowser):
    bowser.get("http://127.0.0.1:5000/home")

