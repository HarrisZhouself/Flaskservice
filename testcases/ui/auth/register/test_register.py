from http.client import responses
from selenium.webdriver.support import expected_conditions as EC

import pytest
import os
import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

current_dir = os.path.dirname(os.path.abspath(__file__))
yaml_path = os.path.join(current_dir, 'testUserData.yaml')

def get_register_userinfo():
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return [(user['username'], user['password'],user['valid']) for user in data['register_test_user_info']]

class TestRegisterPage:

    @pytest.mark.UI
    @pytest.mark.parametrize("a,b,valid", get_register_userinfo())
    def test_register_user(self, browser, client, a, b, valid):

        browser.get("http://127.0.0.1:5000/auth/register")

        register_username_input = browser.find_element(By.ID, "username")
        register_password_input = browser.find_element(By.ID, "password")
        register_button = browser.find_element(By.ID, "register_submit")

        register_username_input.send_keys(a)
        register_password_input.send_keys(b)
        register_button.click()

        if valid:
            try:
                WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, f"//*[contains(text(), '注册成功！')]")
                    ),
                    f"Expect success, active failed"
                )
            except Exception as e:
                browser.save_screenshot(f"register_output_expect_success.png")
                raise
        else:
            try:
                WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, f"//*[contains(text(), '注册失败')]")
                    ),
                    f"Expect failed, active success"
                )
            except Exception as e:
                browser.save_screenshot(f"register_output_expect_failed.png")
                raise