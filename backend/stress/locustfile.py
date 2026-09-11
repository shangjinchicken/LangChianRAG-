"""Locust 压测脚本 —— RAG 企业级知识库问答系统

场景（用 --user-classes 选择对应类，run.bat 里 s0~s4 会自动映射）：
  s0 SmokeUser   冒烟：1 并发，走通 注册→登录→建会话→SSE 聊天→拉历史
  s1 AuthUser    认证基线：register / login / me，聚焦 bcrypt 与 JWT 开销
  s2 ChatUser    问答主路径（核心）：登录→建会话→SSE 聊天，随机问题走完整 RAG 链路
  s3 CacheUser   缓存命中：固定同一问题反复问，验证语义缓存
  s4 WriteUser   写路径：admin 并发上传文档（触发 Embedding + Chroma 写入）

用法示例（在 backend 目录下，User 类名放在命令末尾）：
  venv\\Scripts\\python -m locust -f stress/locustfile.py --host http://localhost:8001 \\
      --users 100 --spawn-rate 5 --run-time 10m --csv results/s2 ChatUser

指标说明：
  - login/register/me/创建会话/上传 等接口：Locust 自动计时，直接看统计。
  - SSE 聊天：自定义上报了两条指标
      SSE /chat-ttft   首个 token 延迟（毫秒）
      SSE /chat-total  完整回答耗时（毫秒）
    自动生成的 "chat" 请求条目时间只是 HTTP 头部返回时间，忽略它。
  - 429 视为「百炼限流」，在统计里以 status 列体现，不自动判失败。
"""
import itertools
import json
import os
import random
import time
import uuid

from locust import HttpUser, between, events, task

HERE = os.path.dirname(os.path.abspath(__file__))

# 与 seed.py 保持一致：预置用户前缀 + 共用密码
USER_PREFIX = "load_user_"
SEED_PASSWORD = "LoadTest123!"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"

_user_seq = itertools.count(1)


def _load_questions():
    p = os.path.join(HERE, "data", "questions.txt")
    with open(p, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


QUESTIONS = _load_questions()
FIXED_QUESTION = "你们的退换货政策是什么？"  # S3 固定问题


def next_username():
    return f"{USER_PREFIX}{next(_user_seq):04d}"


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def try_login(client, username, password):
    """静默登录（不标记失败），返回 token 或 None。用于 on_start 预置用户回退。"""
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    return r.json().get("access_token") if r.status_code == 200 else None


def ensure_login_and_conversation(client):
    """登录（预置用户，未预置则现场注册）并建会话。返回 (token, conv_id)。"""
    username = next_username()
    token = try_login(client, username, SEED_PASSWORD)
    if not token:
        client.post("/api/auth/register",
                    json={"username": username, "password": SEED_PASSWORD})
        token = try_login(client, username, SEED_PASSWORD)
    conv_id = None
    if token:
        r = client.post("/api/conversations", json={"title": "压测会话"},
                        headers=auth_headers(token))
        if r.status_code == 200:
            conv_id = r.json().get("id")
    return token, conv_id


def stream_chat(client, conv_id, token, question):
    """发 SSE 聊天请求，读完整流，上报 ttft / total 两条自定义指标。"""
    url = f"/api/conversations/{conv_id}/chat"
    headers = auth_headers(token)
    start = time.perf_counter()
    first_token_ts = None
    done = False
    err = None

    def report_metrics(ok, total_ms, ttft_ms, msg):
        exc = None if ok else Exception(msg)
        events.request.fire(request_type="SSE", name="/chat-total",
                            response_time=total_ms, response_length=0, exception=exc)
        if ttft_ms is not None:
            events.request.fire(request_type="SSE", name="/chat-ttft",
                                response_time=ttft_ms, response_length=0, exception=exc)

    try:
        with client.post(url, json={"message": question}, headers=headers,
                         stream=True, catch_response=True) as resp:
            if resp.status_code != 200:
                body = resp.text[:200]
                resp.failure(f"chat HTTP {resp.status_code}")
                report_metrics(False, 0, None, f"HTTP {resp.status_code}: {body}")
                return
            for raw in resp.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data:"):
                    continue
                payload = raw[5:].strip()
                if not payload:
                    continue
                try:
                    obj = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                typ = obj.get("type")
                if typ == "token" and first_token_ts is None:
                    first_token_ts = time.perf_counter()
                elif typ == "done":
                    done = True
                elif typ == "error":
                    err = obj.get("content", "chat stream error")
            resp.success()
    except Exception as e:
        err = str(e)

    total_ms = (time.perf_counter() - start) * 1000
    ttft_ms = (first_token_ts - start) * 1000 if first_token_ts else None
    if not done and err is None:
        err = "stream ended without done"
    report_metrics(done and err is None, total_ms, ttft_ms, err)


# ===== S2 / S3 问答基类 =====
class _ChatBase(HttpUser):
    abstract = True
    wait_time = between(2, 8)  # 模拟用户阅读答案的思考时间

    def on_start(self):
        self.token, self.conv_id = ensure_login_and_conversation(self.client)

    def pick_question(self):  # 子类覆盖
        raise NotImplementedError

    @task
    def ask(self):
        if not self.token or not self.conv_id:
            return
        stream_chat(self.client, self.conv_id, self.token, self.pick_question())


class ChatUser(_ChatBase):
    """问答主路径：随机问题 + 唯一后缀，强制绕过语义缓存，走完整 RAG 链路。"""
    def pick_question(self):
        return random.choice(QUESTIONS) + f" [uid:{uuid.uuid4().hex[:6]}]"


class CacheUser(_ChatBase):
    """缓存命中：固定问题，验证语义缓存命中后的低延迟。"""
    def pick_question(self):
        return FIXED_QUESTION


# ===== S1 认证基线 =====
class AuthUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        self.username = next_username()
        self.token = try_login(self.client, self.username, SEED_PASSWORD)

    @task(5)
    def login(self):
        self.client.post("/api/auth/login",
                         json={"username": self.username, "password": SEED_PASSWORD})

    @task(3)
    def register(self):
        u = f"reg_{uuid.uuid4().hex[:12]}"
        self.client.post("/api/auth/register",
                         json={"username": u, "password": "Stress123!",
                               "email": f"{u}@test.com"})

    @task(2)
    def me(self):
        if self.token:
            self.client.get("/api/auth/me", headers=auth_headers(self.token))


# ===== S4 写路径（admin 上传文档）=====
class WriteUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.token = try_login(self.client, ADMIN_USERNAME, ADMIN_PASSWORD)

    @task
    def upload(self):
        if not self.token:
            return
        doc_path = os.path.join(HERE, "data", "sample_docs", "faq_retail.txt")
        with open(doc_path, "rb") as f:
            self.client.post(
                "/api/knowledge/upload",
                files={"file": ("faq_retail.txt", f, "text/plain")},
                headers=auth_headers(self.token),
            )

    @task(3)
    def list_documents(self):
        if self.token:
            self.client.get("/api/knowledge/documents", headers=auth_headers(self.token))


# ===== S0 冒烟 =====
class SmokeUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.username = f"smoke_{uuid.uuid4().hex[:8]}"
        self.client.post("/api/auth/register",
                         json={"username": self.username, "password": "Smoke123!"})
        self.token = try_login(self.client, self.username, "Smoke123!")
        self.conv_id = None
        if self.token:
            r = self.client.post("/api/conversations", json={"title": "冒烟会话"},
                                 headers=auth_headers(self.token))
            if r.status_code == 200:
                self.conv_id = r.json().get("id")

    @task
    def full_flow(self):
        if self.token and self.conv_id:
            stream_chat(self.client, self.conv_id, self.token, FIXED_QUESTION)
            self.client.get(f"/api/conversations/{self.conv_id}/messages",
                            headers=auth_headers(self.token))
