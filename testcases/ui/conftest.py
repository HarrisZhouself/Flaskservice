import pytest
from selenium import webdriver


COMMON_BROWSER_OPTIONS = {
    "no-sandbox": True,
    "disable-shm-usage": True,
    # "headless": True  # 默认无头模式，调试时可注释掉
}

def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="firefox",
        choices=["firefox", "chrome", "edge"],
        help="Browser to run tests: firefox, chrome or edge"
    )
    parser.addoption(
        "--headless",
        action="store_true",
        help="Run tests in headless mode"
    )


@pytest.fixture(scope="function")
def browser(request, app):
    #浏览器实例fixture
    browser_name = request.config.getoption("--browser")
    headless = request.config.getoption("--headless")

    driver = None

    try:
        if browser_name == "firefox":
            options = webdriver.FirefoxOptions()
            for arg, value in COMMON_BROWSER_OPTIONS.items():
                if value is True:
                    options.add_argument(f"--{arg}")
            if headless:
                options.add_argument("--headless")
            driver = webdriver.Firefox(options=options)

        elif browser_name == "chrome":
            options = webdriver.ChromeOptions()
            for arg, value in COMMON_BROWSER_OPTIONS.items():
                if value is True:
                    options.add_argument(f"--{arg}")
            if headless:
                options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)

        elif browser_name == "edge":
            options = webdriver.EdgeOptions()
            for arg, value in COMMON_BROWSER_OPTIONS.items():
                if value is True:
                    options.add_argument(f"--{arg}")
            if headless:
                options.add_argument("--headless")
            driver = webdriver.Edge(options=options)

        driver.implicitly_wait(10)  # 隐式等待10秒
        driver.set_window_size(1280, 720)  # 设置浏览器窗口大小

        yield driver

    finally:
        if driver is not None:
            driver.quit()