import csv
import json
import os

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

# 生成基于时间的唯一目录名
TEST_SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_DIR = f"report/{TEST_SESSION_ID}"

os.makedirs(RESULTS_DIR, exist_ok=True)

def get_filename(prefix, extension):
    """生成文件名（不再需要时间戳，因为目录已经区分）"""
    return f"{RESULTS_DIR}/{prefix}.{extension}"

@events.quitting.add_listener
def export_results(environment, **kwargs):
    print(f"\n所有测试结果保存在: {RESULTS_DIR}")
    """测试结束时导出各种结果"""
    export_stats_to_csv(environment)
    export_failures_to_csv(environment)
    export_percentiles_to_json(environment)
    export_distribution_to_csv(environment)
    generate_html_report(environment)


def export_stats_to_csv(environment):
    """导出基本统计数据到CSV"""
    filename = get_filename("stats", "csv")

    with open(filename, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        # 写入标题行
        writer.writerow([
            "Name", "Type", "# Requests", "# Failures",
            "Median (ms)", "Average (ms)", "Min (ms)",
            "Max (ms)", "Requests/s", "Total Traffic (MB)"
        ])

        # 写入每个端点的统计数据
        stats = environment.stats
        for name, stat in stats.entries.items():
            if stat.num_requests > 0:
                writer.writerow([
                    name,
                    "request",
                    stat.num_requests,
                    stat.num_failures,
                    stat.median_response_time,
                    stat.avg_response_time,
                    stat.min_response_time or 0,
                    stat.max_response_time,
                    stat.total_rps,
                    round(stat.total_content_length / (1024 * 1024), 2)  # 转换为MB
                ])

        # 写入总计行
        writer.writerow([
            "Total",
            "total",
            stats.total.num_requests,
            stats.total.num_failures,
            stats.total.median_response_time,
            stats.total.avg_response_time,
            stats.total.min_response_time or 0,
            stats.total.max_response_time,
            stats.total.total_rps,
            round(stats.total.total_content_length / (1024 * 1024), 2)
        ])

    print(f"\nStatistics exported to {filename}")


def export_failures_to_csv(environment):
    """导出失败请求到CSV"""
    filename = get_filename("failures", "csv")

    with open(filename, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Method", "Name", "Error", "Occurrences"
        ])

        for error in environment.stats.errors.values():
            writer.writerow([
                error.method,
                error.name,
                str(error.error),
                error.occurrences
            ])

    print(f"Failure details exported to {filename}")


def export_percentiles_to_json(environment):
    """导出百分位数据到JSON"""
    filename = get_filename("percentiles", "json")

    percentiles = {
        "total": {
            "50%": environment.stats.total.get_response_time_percentile(0.5),
            "75%": environment.stats.total.get_response_time_percentile(0.75),
            "90%": environment.stats.total.get_response_time_percentile(0.9),
            "95%": environment.stats.total.get_response_time_percentile(0.95),
            "99%": environment.stats.total.get_response_time_percentile(0.99)
        },
        "endpoints": {}
    }

    for name, stat in environment.stats.entries.items():
        if stat.num_requests > 0:
            percentiles["endpoints"][name] = {
                "50%": stat.get_response_time_percentile(0.5),
                "75%": stat.get_response_time_percentile(0.75),
                "90%": stat.get_response_time_percentile(0.9),
                "95%": stat.get_response_time_percentile(0.95),
                "99%": stat.get_response_time_percentile(0.99)
            }

    with open(filename, "w") as jsonfile:
        json.dump(percentiles, jsonfile, indent=2)

    print(f"Percentile data exported to {filename}")


def export_distribution_to_csv(environment):
    """导出响应时间分布到CSV"""
    filename = get_filename("distribution", "csv")

    with open(filename, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "Name", "0-100ms", "100-200ms", "200-300ms",
            "300-400ms", "400-500ms", "500-1000ms", "1-2s",
            "2-3s", "3-4s", "4-5s", "5-10s", "10s+"
        ])

        for name, stat in environment.stats.entries.items():
            if stat.num_requests > 0:
                dist = stat.response_time_distribution()
                writer.writerow([
                    name,
                    dist[(0, 100)],
                    dist[(100, 200)],
                    dist[(200, 300)],
                    dist[(300, 400)],
                    dist[(400, 500)],
                    dist[(500, 1000)],
                    dist[(1000, 2000)],
                    dist[(2000, 3000)],
                    dist[(3000, 4000)],
                    dist[(4000, 5000)],
                    dist[(5000, 10000)],
                    dist[(10000, None)]
                ])

    print(f"Response time distribution exported to {filename}")


def generate_html_report(environment):
    """生成HTML格式的测试报告"""
    filename = get_filename("report", "html")

    stats = environment.stats
    total = stats.total

    # 计算成功率
    success_rate = (total.num_requests - total.num_failures) / total.num_requests * 100 if total.num_requests > 0 else 0

    # 创建HTML内容
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Locust Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
            .metric {{ margin-bottom: 10px; }}
            .metric-name {{ font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .success {{ color: green; }}
            .warning {{ color: orange; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Locust Performance Test Report</h1>
        <div class="summary">
            <h2>Test Summary</h2>
            <div class="metric">
                <span class="metric-name">Total Requests:</span> {total.num_requests}
            </div>
            <div class="metric">
                <span class="metric-name">Failures:</span> {total.num_failures}
            </div>
            <div class="metric">
                <span class="metric-name">Success Rate:</span> 
                <span class="{'success' if success_rate >= 95 else 'warning' if success_rate >= 80 else 'error'}">
                    {success_rate:.2f}%
                </span>
            </div>
            <div class="metric">
                <span class="metric-name">Average Response Time:</span> {total.avg_response_time:.2f} ms
            </div>
            <div class="metric">
                <span class="metric-name">Requests per Second:</span> {total.total_rps:.2f}
            </div>
            <div class="metric">
                <span class="metric-name">Total Traffic:</span> {total.total_content_length / (1024 * 1024):.2f} MB
            </div>
        </div>

        <h2>Endpoint Statistics</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Requests</th>
                <th>Failures</th>
                <th>Avg (ms)</th>
                <th>Min (ms)</th>
                <th>Max (ms)</th>
                <th>RPS</th>
            </tr>
    """

    # 添加每个端点的数据行
    for name, stat in stats.entries.items():
        if stat.num_requests > 0:
            html_content += f"""
            <tr>
                <td>{name}</td>
                <td>{stat.num_requests}</td>
                <td>{stat.num_failures}</td>
                <td>{stat.avg_response_time:.2f}</td>
                <td>{stat.min_response_time or 0}</td>
                <td>{stat.max_response_time}</td>
                <td>{stat.total_rps:.2f}</td>
            </tr>
            """

    html_content += """
        </table>

        <h2>Error Details</h2>
        <table>
            <tr>
                <th>Method</th>
                <th>Name</th>
                <th>Error</th>
                <th>Occurrences</th>
            </tr>
    """

    # 添加错误详情
    for error in stats.errors.values():
        html_content += f"""
        <tr>
            <td>{error.method}</td>
            <td>{error.name}</td>
            <td>{str(error.error)}</td>
            <td>{error.occurrences}</td>
        </tr>
        """

    html_content += """
        </table>
    </body>
    </html>
    """

    with open(filename, "w") as htmlfile:
        htmlfile.write(html_content)

    print(f"HTML report generated at {filename}")


MAX_REPORTS = 10  # 保留最近10次测试结果


def cleanup_old_reports():
    if not os.path.exists("report"):
        return

    reports = sorted(os.listdir("report"), reverse=True)
    for old_dir in reports[MAX_REPORTS:]:
        old_path = os.path.join("report", old_dir)
        if os.path.isdir(old_path):
            import shutil
            shutil.rmtree(old_path)


# 在export_results开始时调用
cleanup_old_reports()