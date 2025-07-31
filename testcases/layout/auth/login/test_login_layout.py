class TestLoginPageLayout:
    # 测试login页面
    def test_login_page(self, client):
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert '用户登录'.encode('utf_8') in response.data
        assert '用户名'.encode('utf_8') in response.data
        assert '密码'.encode('utf_8') in response.data
        assert '登录'.encode('utf_8') in response.data
        assert '还没有账号？'.encode('utf_8') in response.data