import pytest
from app import User
class TestLogin:
#测试login页面
    def test_login_page(self, client):
        response = client.get('/login')
        assert response.status_code == 200
        assert '用户登录'.encode('utf_8') in response.data
        assert '用户名'.encode('utf_8') in response.data
        assert '密码'.encode('utf_8') in response.data
        assert '登录'.encode('utf_8') in response.data
        assert '还没有账号？'.encode('utf_8') in response.data

class TestRegisterPage:
    #测试正常注册是否成功
    @pytest.mark.parametrize("a,b",[('testUser_name0','3edc$RFV'),('testUser_name1','4rfv%TGB'),('testUser_name2','5tgb^YHN'),('testUser_name3','6yhn&UJM'),('testUser_name4','8ik,(OL>')])
    def test_register_redirect(self, client,a,b):

        response = client.post('/register', data = {
            'username': a,
            'password': b
        }, follow_redirects = True)


        assert response.status_code == 200
        assert '用户登录' in response.get_data(as_text=True)
        assert '注册成功！请登录' in response.get_data(as_text=True)


    #边界值法测试登录
    @pytest.mark.xfail
    @pytest.mark.parametrize("a,b",[('testUser_name5','3e#Cc^G'),('testUser_name6',''),('testUser_name7','5tgb^YHN9'),('testUser_name8','6'),('testUser_name9','8ik(OL>sdfioshfisndfggkdjgishgnsdfgjsodighuihrngjsaerjtoierutiweryhngjdafl;kflaope[ruitrehrnlkgfmoaierjtpjwpeork3927489236rrjdn39824yq78324658rghbIKJWQALNEDO;23IU4P973Y28904777Y3HURENJ;WQAJE0-93247890326YRHUEWRJlKRLwejr9i823yrhujwakndl;sekjrtftopie7uqrt9804ehrlka;fjes;lfkjeroitupqoierutierngfpo9843798htgjiok')])
    def test_invalid_less8_password_message(self, client, a, b):

        response = client.post('/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        assert '密码长度至少8个字符' in response.get_data(as_text=True)


    #输入错误信息查看是否失败---失败验证
    @pytest.mark.xfail
    @pytest.mark.parametrize("a,b",[('testUser_name10','3edc$sdf')])
    def test_invalid_need_upper_password_message(self, client,a,b):

        response = client.post('/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        assert '密码必须包含至少一个大写字母' in response.get_data(as_text=True)

    #控制其他变量，更改其中一个，查看是否成功验证
    @pytest.mark.xfail
    @pytest.mark.parametrize("a,b",[('testUser_name11','3WFCC$SDFE')])
    def test_invalid_need_lower_password_message(self, client, a, b):

        response = client.post('/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        assert '密码必须包含至少一个小写字母' in response.get_data(as_text=True)

    #控制其他变量，更改其中一个，查看是否成功验证
    @pytest.mark.xfail
    @pytest.mark.parametrize("a,b",[('testUser_name12','sdWFCC$SDFE')])
    def test_invalid_need_number_password_message(self, client,a,b):


        response = client.post('/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        assert '密码必须包含至少一个数字' in response.get_data(as_text=True)

    #控制其他变量，更改其中一个，查看是否成功验证
    @pytest.mark.xfail
    @pytest.mark.parametrize("a,b",[('testUser_name13','sdWFCC4546SDFE')])
    def test_invalid_need_special_char_password_message(self, client,a, b):

        response = client.post('/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        assert '密码必须包含至少一个特殊字符' in response.get_data(as_text=True)

class TestUserActive:
    #模拟用户注册后登录----场景模拟法
    @pytest.mark.parametrize("a,b",[('testUser_name14','3edc$RFV'),('testUser_name15','4rfv%TGB'),('testUser_name16','5tgb^YHN'),('testUser_name17','6yhn&UJM'),('testUser_name18','8ik,(OL>')])
    def test_register_then_login(self, client,a, b):


        response = client.post('/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        response = client.post('/login', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        assert response.status_code == 200
        assert '欢迎,' in response.get_data(as_text=True)


    #模拟用户注册登录成功后退出，查看是否成功 --用户场景模拟法
    @pytest.mark.parametrize("a,b",[('testUser_name19','1qaz@WSX')])
    def test_logout(self, client , a, b):

        response = client.post('/register', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        response = client.post('/login', data = {
            'username': a,
            'password': b,
        }, follow_redirects = True)

        # 然后登出
        response = client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        assert '用户登录'.encode('utf_8') in response.data


