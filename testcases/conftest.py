import pytest
from app import db, User
from app import app as flask_app
from werkzeug.security import generate_password_hash
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions



def pytest_addoption(parser):
    parser.addoption("--browser", action ="store", default="firefox",
                     help="browser to run tests: chrome or firefox")


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    yield flask_app


@pytest.fixture
def client(app):
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture(scope="function")
def browser(request):
    browser_name = request.config.getoption("--browser")
    if browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        #options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-shm-usage")
        driver = webdriver.Firefox(options=options)
    elif  browser_name == "edge":
        options = webdriver.EdgeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-shm-usage")
        driver = webdriver.Firefox(options=options)
    else:
        raise ValueError(f"Unsupported browser {browser_name}")

    yield driver
    driver.quit()


def test_home_page(bowser):
    bowser.get("http://127.0.0.1:5000/home")

