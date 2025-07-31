class TestRegisterPageLayout:
    # 测试Register页面
    def test_login_page(self, client):
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert '用户注册'.encode('utf_8') in response.data
        assert '用户名'.encode('utf_8') in response.data
        assert '密码'.encode('utf_8') in response.data
        assert '登录'.encode('utf_8') in response.data
        assert '至少8个字符'.encode('utf_8') in response.data
        assert '至少一个大写字母'.encode('utf_8') in response.data
        assert '至少一个小写字母'.encode('utf_8') in response.data
        assert '至少一个数字'.encode('utf_8') in response.data
        assert '至少一个特殊字符'.encode('utf_8') in response.data
        assert '已有账号？'.encode('utf_8') in response.data