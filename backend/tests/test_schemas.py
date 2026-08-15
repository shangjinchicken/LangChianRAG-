"""Pydantic Schema 校验单元测试"""
import pytest
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
)
from app.schemas.chat import ChatRequest, SourceInfo, ChatStreamChunk
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageResponse,
)
from app.schemas.knowledge import (
    DocumentResponse,
    DocumentListResponse,
    KnowledgeStatsResponse,
)


class TestRegisterRequest:
    """注册请求校验"""

    def test_正常输入校验通过(self):
        """正常用户名和密码应通过 Pydantic 验证"""
        req = RegisterRequest(username="testuser", password="123456")
        assert req.username == "testuser"
        assert req.password == "123456"
        assert req.email is None

    def test_带邮箱注册校验通过(self):
        """提供可选邮箱字段也应通过"""
        req = RegisterRequest(username="alice", password="abcdef", email="alice@test.com")
        assert req.email == "alice@test.com"

    def test_用户名过短报错(self):
        """用户名最少 2 个字符"""
        with pytest.raises(Exception):
            RegisterRequest(username="a", password="123456")

    def test_密码过短报错(self):
        """密码最少 6 个字符"""
        with pytest.raises(Exception):
            RegisterRequest(username="user123", password="12345")

    def test_用户名过长报错(self):
        """用户名最多 50 个字符"""
        with pytest.raises(Exception):
            RegisterRequest(username="x" * 51, password="123456")

    def test_缺少必填字段报错(self):
        """缺少 username 字段应报错"""
        with pytest.raises(Exception):
            RegisterRequest(password="123456")  # type: ignore


class TestLoginRequest:
    """登录请求校验"""

    def test_正常输入校验通过(self):
        """正常用户名和密码"""
        req = LoginRequest(username="admin", password="123456")
        assert req.username == "admin"

    def test_缺少密码报错(self):
        """缺少 password 字段"""
        with pytest.raises(Exception):
            LoginRequest(username="admin")  # type: ignore


class TestChangePasswordRequest:
    """改密请求校验"""

    def test_正常输入校验通过(self):
        """新旧密码均符合长度要求"""
        req = ChangePasswordRequest(old_password="oldpass", new_password="newpass123")
        assert req.old_password == "oldpass"
        assert req.new_password == "newpass123"

    def test_新密码过短报错(self):
        """新密码至少 6 个字符"""
        with pytest.raises(Exception):
            ChangePasswordRequest(old_password="oldpass", new_password="12345")


class TestChatRequest:
    """问答请求校验"""

    def test_正常消息校验通过(self):
        """非空消息应通过"""
        req = ChatRequest(message="请问有什么商品？")
        assert req.message == "请问有什么商品？"

    def test_空消息报错(self):
        """消息不能为空字符串"""
        with pytest.raises(Exception):
            ChatRequest(message="")


class TestSourceInfo:
    """引用来源 Schema"""

    def test_正常创建来源信息(self):
        s = SourceInfo(filename="test.pdf", snippet="这是片段内容", page=3)
        assert s.filename == "test.pdf"
        assert s.page == 3

    def test_page和chunk_index可选(self):
        """页码和分块序号是可选的"""
        s = SourceInfo(filename="doc.txt", snippet="内容片段")
        assert s.page is None
        assert s.chunk_index is None


class TestChatStreamChunk:
    """SSE 流式块 Schema"""

    def test_token类型(self):
        chunk = ChatStreamChunk(type="token", content="你好")
        assert chunk.type == "token"
        assert chunk.content == "你好"

    def test_done类型(self):
        chunk = ChatStreamChunk(type="done")
        assert chunk.type == "done"

    def test_error类型(self):
        chunk = ChatStreamChunk(type="error", content="生成失败")
        assert chunk.type == "error"
        assert chunk.content == "生成失败"


class TestConversationSchemas:
    """会话 Schema 校验"""

    def test_创建会话默认标题(self):
        c = ConversationCreate()
        assert c.title == "新会话"

    def test_创建会话自定义标题(self):
        c = ConversationCreate(title="商品咨询")
        assert c.title == "商品咨询"

    def test_标题过长报错(self):
        """标题最长 200 字符"""
        with pytest.raises(Exception):
            ConversationCreate(title="x" * 201)

    def test_更新会话标题(self):
        u = ConversationUpdate(title="新标题")
        assert u.title == "新标题"

    def test_更新空标题报错(self):
        """更新标题不能为空"""
        with pytest.raises(Exception):
            ConversationUpdate(title="")


class TestKnowledgeSchemas:
    """知识库 Schema"""

    def test_DocumentResponse创建(self):
        d = DocumentResponse(
            id="doc-1",
            filename="test.pdf",
            file_size=1024,
            file_type="pdf",
            chunk_count=5,
            status="completed",
        )
        assert d.filename == "test.pdf"
        assert d.chunk_count == 5

    def test_DocumentListResponse创建(self):
        items = [
            DocumentResponse(
                id="1", filename="a.pdf", file_size=100,
                file_type="pdf", chunk_count=2, status="completed",
            )
        ]
        resp = DocumentListResponse(total=1, items=items)
        assert resp.total == 1
        assert len(resp.items) == 1

    def test_KnowledgeStatsResponse创建(self):
        stats = KnowledgeStatsResponse(
            document_count=10,
            total_chunks=150,
            total_size=1024000,
        )
        assert stats.document_count == 10
        assert stats.total_chunks == 150

    def test_ConversationResponse创建(self):
        resp = ConversationResponse(
            id="conv-1",
            user_id="user-1",
            title="测试会话",
            message_count=5,
        )
        assert resp.id == "conv-1"
        assert resp.message_count == 5
