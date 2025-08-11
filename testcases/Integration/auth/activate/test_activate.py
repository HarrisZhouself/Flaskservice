import os
import pytest
import yaml
from flask import url_for

current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建yaml文件的完整路径
yaml_path = os.path.join(current_dir, 'testUserData.yaml')

def get_activate_test_user_info():
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return [(user['username'], user['password']) for user in data['activate_test_user_info']]


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

    assert loginResponse.status_code == 200
    assert '欢迎' in loginResponse.get_data(as_text=True)
    assert '您已成功登录系统' in loginResponse.get_data(as_text=True)

    response = client.get('/logout', follow_redirects=True)

    return (response.status_code == 200
            and '用户登录'.encode('utf_8') in response.data
            and '您已安全退出'.encode('utf_8') in response.data)

class TestActivate:

    @pytest.mark.parametrize("username, password", get_activate_test_user_info())
    def test_activate(self, client, username, password):

        if init_test(client,username, password):
            reLoginResponse = client.post('/auth/login', data={
                'username': username,
                'password': password,
            }, follow_redirects=True)

            assert reLoginResponse.status_code == 200
            assert '账户未激活，请先激活账户'.encode('utf_8') in reLoginResponse.data

            toActiveResponse = client.get(url_for('auth.activate'), follow_redirects=True)
            assert toActiveResponse.status_code == 200
            assert '账户激活'.encode('utf_8') in toActiveResponse.data
            assert toActiveResponse.request.path == url_for('auth.activate')

            activateResponse = client.post('/auth/activate', data={
                'username': username,
                'password': password,
            }, follow_redirects=True)

            assert activateResponse.status_code == 200
            assert '账户已激活，请登录'.encode('utf_8') in activateResponse.data
            assert activateResponse.request.path == url_for('auth.login')

            finalResponse = client.post('/auth/login', data={
                'username': username,
                'password': password,
            }, follow_redirects=True)

            assert finalResponse.status_code == 200
            assert '欢迎' in finalResponse.get_data(as_text=True)
            assert finalResponse.request.path == url_for('core.home')
            assert '您已成功登录系统' in finalResponse.get_data(as_text=True)

        else:
            print('init_test failed')
