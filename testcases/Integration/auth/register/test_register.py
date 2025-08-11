import os

import pytest
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建yaml文件的完整路径
yaml_path = os.path.join(current_dir, 'testUserData.yaml')

def get_register_test_user_info():
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    return [(user['username'], user['password'],user['valid']) for user in data['register_test_user_info']]


class TestRegister:

    #测试正常注册是否成功
    @pytest.mark.parametrize("a, b, valid", get_register_test_user_info())
    def test_register(self, client, a, b, valid):

        response = client.post('/auth/register', data={
            'username': a,
            'password': b,
        }, follow_redirects=True)

        if valid:
            # 预期成功：检查是否跳转到登录页
            assert response.status_code == 200
            assert '用户登录' in response.get_data(as_text=True)
            assert '注册成功！请登录' in response.get_data(as_text=True)
        else:
            # 预期失败：检查是否仍在注册页，并显示错误
            assert response.status_code == 200  # 或 400（取决于 API 设计）
            assert '注册失败' in response.get_data(as_text=True)# 确保返回注册页
