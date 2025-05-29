from locust import HttpUser, task, between
import random
import string


def random_string(length=8):
    """生成随机字符串"""
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # 用户等待时间1-3秒

    @task(3)  # 登录任务权重3
    def login(self):
        # 使用已存在的测试用户登录
        username = "testuser"
        password = "Testpass1!"
        self.client.post("/login", data={
            "username": username,
            "password": password
        })

    @task(1)  # 注册任务权重1
    def register(self):
        # 注册新用户
        username = f"testUser_{random_string(6)}"
        password = f"Pass{random.randint(1000, 9999)}!"
        self.client.post("/register", data={
            "username": username,
            "password": password
        })

    def on_start(self):
        """每个用户开始时执行"""
        # 可以在这里添加初始化操作
        pass