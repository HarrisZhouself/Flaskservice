import os
import pytest
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建yaml文件的完整路径
yaml_path = os.path.join(current_dir, 'testUserData.yaml')

def get_login_test_user_info():
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return [(user['registerUsername'], user['registerPassword'],user['loginUsername'], user['loginPassword'],user['valid'],user['expect_error']) for user in data['login_test_user_info']]


def init_test(client, registerUsername, registerPassword, loginUsername,  loginPassword):

    registerResponse = client.post('/auth/register', data={
        'username': registerUsername,
        'password': registerPassword,
    }, follow_redirects=True)

    assert registerResponse.status_code == 200
    assert '用户登录' in registerResponse.get_data(as_text=True)
    assert '注册成功！请登录' in registerResponse.get_data(as_text=True)

    loginResponse = client.post('/auth/login', data={
        'username': loginUsername,
        'password': loginPassword,
    }, follow_redirects=True)

    return loginResponse

class TestLogin:

    @pytest.mark.parametrize("registerUsername, registerPassword,loginUsername, loginPassword, valid, expect_error", get_login_test_user_info())
    def test_login(self, client, registerUsername, registerPassword, loginUsername,  loginPassword, valid, expect_error):

        response = init_test(client,registerUsername, registerPassword, loginUsername,  loginPassword)

        if valid:
            # 预期成功：检查是否跳转到home页
            assert response.status_code == 200
            assert '欢迎' in response.get_data(as_text=True)
            assert '您已成功登录系统' in response.get_data(as_text=True)

        else:
            if expect_error is 'username_error':
                # 预期失败：检查是否仍在登录页，并显示错误
                assert response.status_code == 200  # 或 400（取决于 API 设计）
                assert '用户登录' in response.get_data(as_text=True)# 确保返回注册页
                assert '帐户不存在' in response.get_data(as_text=True)

            if expect_error is 'password_error':
                # 预期失败：检查是否仍在登录页，并显示错误
                assert response.status_code == 200  # 或 400（取决于 API 设计）
                assert '用户登录' in response.get_data(as_text=True)  # 确保返回注册页
                assert '密码错误，您还有 4 次尝试机会' in response.get_data(as_text=True)
