import pytest
from app import User
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class TestUI:
    @pytest.mark.UI
    @pytest.mark.parametrize("a,b", [('testUser_name20', '3edc$RFV')])
    def test_login_ui(self,client, a,b):

        driver = webdriver.Edge()
        try:
            driver.get("http://127.0.0.1:5000/login")
            # 注册凭据并提交
            # api_url = "http://127.0.0.1:5000/register"
            response = client.post('/register', data={
                'username': a,
                'password': b,
            }, follow_redirects=True)
            #验证注册正常
            assert response.status_code == 200


            # 输入凭据并提交
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(a)
            driver.find_element(By.ID, "password").send_keys(b)
            driver.find_element(By.ID, "login_submit").click()

            # 验证登录成功
            # 检查是否跳转到 /home
            WebDriverWait(driver, 10).until(
                EC.url_contains("/home")  # 检查是否跳转到首页
            )

            assert "logout_submit" in driver.page_source  # 检查登出按钮
        finally:
            driver.quit()

    @pytest.mark.UI
    @pytest.mark.parametrize("a,b", [('testUser_name21', '3edc$RFV')])
    def test_logout_submit_ui(self, client, a, b):

        driver = webdriver.Edge()
        try:
            driver.get("http://127.0.0.1:5000/login")
            # 注册凭据并提交
            response = client.post('/register', data={
                'username': a,
                'password': b,
            }, follow_redirects=True)
            # 输入凭据并提交
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(a)
            driver.find_element(By.ID, "password").send_keys(b)
            driver.find_element(By.ID, "login_submit").click()

            # 验证登录成功
            # 检查是否跳转到 /home
            WebDriverWait(driver, 10).until(
                EC.url_contains("/home")  # 检查是否跳转到首页
            )

            driver.find_element(By.ID, "logout_submit").click()

            WebDriverWait(driver, 10).until(
                EC.url_contains("/login")  # 检查是否跳转到登录页
            )

            assert "login_submit" in driver.page_source  # 检查登出按钮
            assert "您已安全退出，在激活后可以重新登录" in driver.page_source

        finally:
            driver.quit()

    @pytest.mark.UI
    @pytest.mark.parametrize("a,b", [('testUser_name22', '3edc$RFV')])
    def test_delete_submit_ui(self,client,a,b):
        driver = webdriver.Edge()
        try:
            driver.get("http://127.0.0.1:5000/login")
            response = client.post('/register', data={
                'username': a,
                'password': b,
            }, follow_redirects=True)

            #输入密码并提交
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(a)
            driver.find_element(By.ID, "password").send_keys(b)
            driver.find_element(By.ID, "login_submit").click()

            #验证登陆成功

            WebDriverWait(driver, 10).until(
                EC.url_contains("/home")
            )

            #注销用户

            driver.find_element(By.ID, "delete_submit").click()

            alert = WebDriverWait(driver, 10).until(
                EC.alert_is_present()
            )
            assert "确定要永久注销账户吗？此操作不可逆！" in alert.text
            alert.accept()

            WebDriverWait(driver, 10).until(
                EC.url_contains("/login")
            )
            assert "您的信息已经清除完毕，感谢使用我们的服务" in driver.page_source
        finally:
            driver.quit()

    @pytest.mark.UI
    @pytest.mark.parametrize("a,b", [('testUser_name23', '3edc$RFV')])
    def test_delete_submit_then_login_ui(self, client, a, b):
        driver = webdriver.Edge()
        try:
            driver.get("http://127.0.0.1:5000/login")
            client.post('/register', data={
                'username': a,
                'password': b,
            }, follow_redirects=True)

            # 输入密码并提交
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(a)
            driver.find_element(By.ID, "password").send_keys(b)
            driver.find_element(By.ID, "login_submit").click()

            # 验证登陆成功

            WebDriverWait(driver, 10).until(
                EC.url_contains("/home")
            )

            # 注销用户

            driver.find_element(By.ID, "delete_submit").click()

            alert = WebDriverWait(driver, 10).until(
                EC.alert_is_present()
            )
            assert "确定要永久注销账户吗？此操作不可逆！" in alert.text
            alert.accept()

            WebDriverWait(driver, 10).until(
                EC.url_contains("/login")
            )

            #重新输入并提交
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys(a)
            driver.find_element(By.ID, "password").send_keys(b)
            driver.find_element(By.ID, "login_submit").click()


            error_message = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "alert-error")))

            assert "账户不存在" in error_message.text

        finally:
            driver.quit()
