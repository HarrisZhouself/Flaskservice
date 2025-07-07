import pytest

class TestUserActive:
    #模拟用户注册后登录----场景模拟法
    @pytest.mark.parametrize("a,b",[('testUser_name14','3edc$RFV'),('testUser_name15','4rfv%TGB'),('testUser_name16','5tgb^YHN'),('testUser_name17','6yhn&UJM'),('testUser_name18','8ik,(OL>')])
    def test_register_then_login(self, client,a, b):
        response = client.post('/auth/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        response = client.post('/auth/login', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        assert response.status_code == 200
        assert '欢迎,' in response.get_data(as_text=True)


    #模拟用户注册登录成功后退出，查看是否成功 --用户场景模拟法
    @pytest.mark.parametrize("a,b",[('testUser_name19','1qaz@WSX')])
    def test_logout(self, client , a, b):

        response = client.post('/auth/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        response = client.post('/auth/login', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        # 然后登出
        response = client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        assert '用户登录'.encode('utf_8') in response.data
