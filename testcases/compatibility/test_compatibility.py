import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestCompatibility:
    @pytest.mark.compatibility
    @pytest.mark.parametrize("browser_name, a, b", [('firefox', 'testUser_name24', '3edc$RFV')])
    def test_login_logout_compatibility(self, request, browser_name, client, browser, a, b):

        browser.get("http://127.0.0.1:5000/register")

        # 测试注册
        register_username_input = browser.find_element(By.ID, "username")
        register_password_input = browser.find_element(By.ID, "password")
        register_button = browser.find_element(By.ID, "register_submit")

        register_username_input.send_keys(a)
        register_password_input.send_keys(b)
        register_button.click()

        WebDriverWait(browser, 10).until(
            EC.url_contains("/login"),
            f"register failed on {browser_name}"
        )

        # 测试登录
        login_username_input = browser.find_element(By.ID, "username")
        login_password_input = browser.find_element(By.ID, "password")
        login_button = browser.find_element(By.ID, "login_submit")

        login_username_input.send_keys(a)
        login_password_input.send_keys(b)
        login_button.click()

        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '欢迎')]")
                ),
                f"Login failed on {browser_name}"
            )
        except Exception as e:
            browser.save_screenshot(f"welcome_failed_{browser_name}.png")
            raise

        logout_button = browser.find_element(By.ID, "logout_submit")
        logout_button.click()

        WebDriverWait(browser, 5).until(
            EC.url_contains("/login"),
            f"Logout failed on {browser_name}"
        )

        # 验证flash消息
        flash_message = browser.find_element(By.CLASS_NAME, "alert-info").text
        assert "您已安全退出，在激活后可以重新登录" in flash_message

        # 激活登录

        login_username_input = browser.find_element(By.ID, "username")
        login_password_input = browser.find_element(By.ID, "password")
        login_button = browser.find_element(By.ID, "login_submit")

        login_username_input.send_keys(a)
        login_password_input.send_keys(b)
        login_button.click()

        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '您的账户当前处于未激活状态，请输入您的用户名和密码来激活账户')]")
                ),
                f"activate failed on {browser_name}"
            )
        except Exception as e:
            browser.save_screenshot(f"activate_failed_{browser_name}.png")
            raise

        activate_username_input = browser.find_element(By.ID, "username")
        activate_password_input = browser.find_element(By.ID, "password")
        activate_button = browser.find_element(By.ID, "activate_submit")

        activate_username_input.send_keys(a)
        activate_password_input.send_keys(b)
        activate_button.click()

        WebDriverWait(browser, 10).until(
            EC.url_contains("/login"),
            f"activate failed on {browser_name}"
        )

        # 激活后登录
        login_username_input = browser.find_element(By.ID, "username")
        login_password_input = browser.find_element(By.ID, "password")
        login_button = browser.find_element(By.ID, "login_submit")

        login_username_input.send_keys(a)
        login_password_input.send_keys(b)
        login_button.click()

        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '欢迎')]")
                ),
                f"Login failed on {browser_name}"
            )
        except Exception as e:
            browser.save_screenshot(f"welcome_failed_{browser_name}.png")
            raise


        delete_button = browser.find_element(By.ID, "delete_submit")
        delete_button.click()

        alert = WebDriverWait(browser, 10).until(
            EC.alert_is_present()
        )
        assert "确定要永久注销账户吗？此操作不可逆！" in alert.text
        alert.accept()

        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '您的信息已经清除完毕，感谢使用我们的服务')]")
                ),
                f"delete failed on {browser_name}"
            )
        except Exception as e:
            browser.save_screenshot(f"delete_failed_{browser_name}.png")
            raise
