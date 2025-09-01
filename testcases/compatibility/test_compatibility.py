import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestCompatibility:
    @pytest.mark.compatibility
    @pytest.mark.parametrize("browser_name, a, b", [('firefox', 'testUser_name24', '3edc$RFV'),('edge', 'testUser_name24', '3edc$RFV')])
    def test_login_logout_compatibility(self, browser_name, client, browser, a, b):

        browser.get("http://127.0.0.1:5000/auth/register")

        # 测试注册
        register_username_input = browser.find_element(By.ID, "username")
        register_password_input = browser.find_element(By.ID, "password")
        register_button = browser.find_element(By.ID, "register_submit")

        register_username_input.send_keys(a)
        register_password_input.send_keys(b)
        register_button.click()

        WebDriverWait(browser, 10).until(
            EC.url_contains("/auth/login"),
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

        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '您已安全退出')]")
                ),
                f"Logout failed on {browser_name}"
            )
        except Exception as e:
            browser.save_screenshot(f"logout_failed_{browser_name}.png")
            raise

        # 激活登录
        # 重新登录，出现激活按钮

        login_username_input = browser.find_element(By.ID, "username")
        login_password_input = browser.find_element(By.ID, "password")
        login_button = browser.find_element(By.ID, "login_submit")

        login_username_input.send_keys(a)
        login_password_input.send_keys(b)
        login_button.click()

        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '账户未激活，请先激活账户')]")
                ),
                f"activate failed on {browser_name}"
            )
        except Exception as e:
            browser.save_screenshot(f"activate_link_failed_discover_{browser_name}.png")
            raise

        activate_link = browser.find_element(By.XPATH, f"//*[contains(text(), '此处')]")
        activate_link.click()

        try:
            WebDriverWait(browser, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '您的账户当前处于未激活状态，请输入您的用户名和密码来激活账户')]")
                ),
                f"activate link drop to activate page failed on {browser_name}"
            )
        except Exception as e:
            browser.save_screenshot(f"activate_link_drop_failed_{browser_name}.png")
            raise

        activate_username_input = browser.find_element(By.ID, "username")
        activate_password_input = browser.find_element(By.ID, "password")
        activate_button = browser.find_element(By.ID, "activate_submit")

        activate_username_input.send_keys(a)
        activate_password_input.send_keys(b)
        activate_button.click()

        WebDriverWait(browser, 10).until(
            EC.url_contains("/auth/login"),
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

        delete_account_password_input = browser.find_element(By.ID, "delete_account_password")
        delete_button = browser.find_element(By.ID, "delete_account_submit")

        delete_account_password_input.send_keys(b)
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
