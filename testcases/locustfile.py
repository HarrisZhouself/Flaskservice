from locust import HttpUser, task, between
import random
import string
from datetime import datetime

def random_name_string(length=8):
    """生成随机字符串"""
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))

def random_string(length=8):
    """
    生成包含大小写字母、数字和特殊字符的随机字符串
    参数:
        length: 需要生成的字符串长度
    返回:
        随机生成的字符串
    """
    # 定义字符池
    characters = (
            string.ascii_uppercase +  # 大写字母 A-Z
            string.ascii_lowercase +  # 小写字母 a-z
            string.digits +  # 数字 0-9
            "!@#$%^&*()_+-=[]{}|;:,.<>?"  # 特殊字符
    )

    # 确保至少包含每种类型字符（如果length>=4）
    if length >= 4:
        return (
                random.choice(string.ascii_uppercase) +  # 至少1个大写
                random.choice(string.ascii_lowercase) +  # 至少1个小写
                random.choice(string.digits) +  # 至少1个数字
                random.choice("!@#$%^&*()_+-=[]{}|;:,.<>?") +  # 至少1个特殊字符
                ''.join(random.choices(characters, k=length - 4))  # 剩余随机字符
        )
    else:
        return ''.join(random.choices(characters, k=length))


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # 用户等待时间1-3秒

    @task(1)  # 登录任务权重3
    def login(self):
        # 使用已存在的测试用户登录
        username = "testuser"
        password = "Testpass1!"
        self.client.post("/login", data={
            "username": username,
            "password": password
        })

    @task(3)  # 注册任务权重1
    def register(self):
        # 1. 生成唯一测试数据（加入时间戳保证唯一性）
        timestamp = int(datetime.now().timestamp() * 1000)
        username = f"testUser_{random_name_string(6)}"
        password = random_string(8)

        # 2. 添加请求头（根据实际情况调整）
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Request-ID": f"locust_{timestamp}"
        }

        # 3. 带错误捕获的请求
        with self.client.post(
                "/register",
                data={
                    "username": username,
                    "password": password
                },
                headers=headers,
                catch_response=True,  # 允许捕获非200响应
                name="/register"  # 单独统计该端点
        ) as response:
            # 4. 自定义成功/失败判断（根据API实际返回调整）
            if response.status_code == 200:
                if "success" in response.text.lower():
                    response.success()
                else:
                    response.failure(f"Unexpected success response: {response.text}")
            elif response.status_code == 409:
                response.failure("Username conflict (retry with new username)")
            else:
                # 5. 记录详细错误信息（便于调试）
                error_msg = f"Status {response.status_code}: {response.text[:200]}"  # 截断长文本
                print(f"FAIL: {error_msg}")  # 控制台输出
                response.failure(error_msg)

    def on_start(self):
        """每个用户开始时执行"""
        # 可以在这里添加初始化操作
        pass