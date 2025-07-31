from locust import HttpUser, task, between, LoadTestShape, events
import re
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


@events.request.add_listener
def on_request_failure(request_type, name, response_time, response_length, exception, context, **kwargs):
    if exception:
        print(f"\nGLOBAL FAILURE: {request_type} {name} | Exception: {exception}")
        print(f"Response time: {response_time}ms | Context: {context}\n")


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # 用户等待时间1-3秒
    csrf_token = None  # 存储CSRF令牌

    @task(1)  # 登录任务权重3
    def login(self):
        # 使用已存在的测试用户登录
        username = "testuser"
        password = "Testpass1!"
        self.client.post("/auth/login",  data={
                    "csrf_token": self.csrf_token,
                    "username": username,
                    "password": password
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": f"{self.host}/auth/register"  # 有些框架需要Referer
                },)

    @task(3)  # 注册任务权重1
    def register(self):
        if not self.csrf_token:
            print("WARNING: CSRF token is missing, skipping register task")
            return

        timestamp = int(datetime.now().timestamp() * 1000)
        username = f"testUser_{random_name_string(6)}_{timestamp}"
        password = random_string(8)

        print(f"DEBUG: Attempting registration - User: {username}, Pass: {password}")

        with self.client.post(
                "/auth/register",
                data={
                    "csrf_token": self.csrf_token,
                    "username": username,
                    "password": password
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": f"{self.host}/auth/register"
                },
                catch_response=True
        ) as response:
            # 记录详细的请求和响应信息
            req_info = f"Request: username={username}, password={password}, csrf={self.csrf_token[:10]}..."
            resp_info = f"Response: status={response.status_code}, time={response.elapsed:.2f}s, text={response.text[:200]}"

            if response.status_code == 200:
                if "success" in response.text.lower():
                    print(f"SUCCESS: Registration succeeded - {req_info}")
                    response.success()
                else:
                    error_msg = f"Unexpected 200 response - {req_info} | {resp_info}"
                    print(f"WARNING: {error_msg}")
                    response.failure(error_msg)
            elif response.status_code == 403 and "CSRF" in response.text:
                error_msg = "CSRF token expired or invalid"
                print(f"ERROR: {error_msg} - {resp_info}")
                self.csrf_token = None  # 强制下次重新获取
                response.failure(error_msg)
            elif response.status_code == 409:
                error_msg = f"Username already exists - {req_info}"
                print(f"CONFLICT: {error_msg}")
                response.failure(error_msg)
            else:
                error_msg = f"Unexpected error - {req_info} | {resp_info}"
                print(f"ERROR: {error_msg}")
                response.failure(error_msg)

    def on_start(self):
        """获取注册页面的CSRF令牌"""
        with self.client.get("/auth/register", catch_response=True) as response:
            if response.status_code == 200:
                match = re.search(
                    r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
                    response.text
                )
                if match:
                    self.csrf_token = match.group(1)
                    print(f"DEBUG: Successfully obtained CSRF token: {self.csrf_token[:10]}...")
                else:
                    error_msg = "CSRF token not found in HTML"
                    print(f"ERROR: {error_msg} - Response: {response.text[:200]}")
                    response.failure(error_msg)
            else:
                error_msg = f"Failed to load register page: {response.status_code}"
                print(f"ERROR: {error_msg} - Response: {response.text[:200]}")
                response.failure(error_msg)


class StepLoadShape(LoadTestShape):
    """
    阶梯式负载测试配置
    参数说明：
        -duration： 持续时间（s）
        -users: 目标用户数
        -spawn_rate： 每秒生成/停止用户数
    """
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 10}, #阶段一： 快速增加到10用户
        {"duration": 120, "users": 50, "spawn_rate": 10}, #阶段2： 用户逐步增加到50用户
        {"duration": 180, "users": 100, "spawn_rate": 20}, #阶段3： 用户快速增加到100
        {"duration": 120, "users": 30, "spawn_rate": 5}, #阶段4： 逐步较少用户到30
    ]

    def tick(self):
        """
        核心方法：根据当前时间返回（user_count, spawn_rate） 或none（停止测试）
        """
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None

