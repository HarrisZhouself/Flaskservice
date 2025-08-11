import os
import pytest
import yaml
import re
from flask import url_for

current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建yaml文件的完整路径
yaml_path = os.path.join(current_dir, 'testUserData.yaml')

def get_deleteAccount_test_user_info():
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return [(user['username'], user['password']) for user in data['delete_test_user_info']]

def get_csrf_token(response):
    match = re.search(r'name="csrf_token"\s+value="(.+?)"', response.get_data(as_text=True))
    return match.group(1) if match else None

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
            and '欢迎' in response_text
            and '您已成功登录系统' in response_text
            and  loginResponse.request.path == url_for('core.home'))


class TestDeleteAccount:
    @pytest.mark.parametrize("username, password", get_deleteAccount_test_user_info())
    def test_account_deletion_flow(self, client, username, password):
        # 1. 初始化测试（注册+登录）
        assert init_test(client, username, password)

        # 2. 获取 CSRF Token
        activate_page = client.get(url_for('auth.activate'))
        csrf_token = get_csrf_token(activate_page)
        assert csrf_token, "CSRF Token 未找到"

        # 3. 提交删除请求
        delete_response = client.post(
            url_for('auth.delete_account'),
            data={'csrf_token': csrf_token, 'password': password},
            follow_redirects=True
        )
        assert delete_response.status_code == 200
        assert '您的信息已经清除完毕' in delete_response.get_data(as_text=True)
        assert delete_response.request.path == url_for('auth.login')

        # 4. 验证账户已删除
        relogin_response = client.post(
            url_for('auth.login'),
            data={'username': username, 'password': password},
            follow_redirects=True
        )
        assert '账户不存在' in relogin_response.get_data(as_text=True)

