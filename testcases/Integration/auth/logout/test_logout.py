import os
import pytest
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建yaml文件的完整路径
yaml_path = os.path.join(current_dir, 'testUserData.yaml')

def get_logout_test_user_info():
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return [(user['username'], user['password']) for user in data['logout_test_user_info']]


def init_test(client, username, password):

    registerResponse = client.post('/auth/register', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)

    assert registerResponse.status_code == 200
    assert '用户登录' in registerResponse.get_data(as_text=True)
    assert '注册成功！请登录' in registerResponse.get_data(as_text=True)

    loginResponse = client.post('/auth/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)

    response_text = loginResponse.get_data(as_text=True)
    return (loginResponse.status_code == 200
            and "欢迎" in response_text
            and '您已成功登录系统' in response_text)

class TestLogout:

    @pytest.mark.parametrize("username, password", get_logout_test_user_info())
    def test_logout(self, client, username, password):

        if init_test(client,username, password):
            response = client.get('/logout', follow_redirects=True)

            assert response.status_code == 200
            assert '用户登录'.encode('utf_8') in response.data
            assert '您已安全退出'.encode('utf_8') in response.data

        else:
            print('init_test failed')
