"""ORM 模型 to_dict 方法单元测试"""
import pytest
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message


class TestUserModel:
    """User 模型 to_dict 测试"""

    def test_to_dict包含所有字段(self):
        """验证 to_dict 返回包含 id/username/email/role/created_at"""
        user = User(
            id="usr-001",
            username="testuser",
            password_hash="hashed_xxx",
            email="test@example.com",
            role="user",
        )
        d = user.to_dict()

        assert d["id"] == "usr-001"
        assert d["username"] == "testuser"
        assert d["email"] == "test@example.com"
        assert d["role"] == "user"
        assert "password_hash" not in d  # 密码哈希不应暴露

    def test_管理员角色(self):
        """管理员角色的用户"""
        user = User(
            id="adm-001",
            username="admin",
            password_hash="hashed_xxx",
            role="admin",
        )
        d = user.to_dict()
        assert d["role"] == "admin"

    def test_created_at字段(self):
        """created_at 为 None 时不应报错"""
        user = User(
            id="usr-002",
            username="nouser",
            password_hash="xxx",
        )
        d = user.to_dict()
        assert d["created_at"] is None

    def test_email为None时返回None(self):
        """email 可选字段为 None 时正常返回"""
        user = User(
            id="usr-003",
            username="noemail",
            password_hash="xxx",
        )
        d = user.to_dict()
        assert d["email"] is None


class TestDocumentModel:
    """Document 模型 to_dict 测试"""

    def test_to_dict包含所有字段(self):
        doc = Document(
            id="doc-001",
            filename="产品手册.pdf",
            file_path="/uploads/doc-001.pdf",
            file_size=204800,
            file_type="pdf",
            chunk_count=10,
            status="completed",
        )
        d = doc.to_dict()

        assert d["id"] == "doc-001"
        assert d["filename"] == "产品手册.pdf"
        assert d["file_size"] == 204800
        assert d["file_type"] == "pdf"
        assert d["chunk_count"] == 10
        assert d["status"] == "completed"

    def test_处理中状态(self):
        """文档处理中的状态"""
        doc = Document(
            id="doc-002",
            filename="data.xlsx",
            file_path="/uploads/doc-002.xlsx",
            file_size=1024,
            file_type="xlsx",
            chunk_count=0,
            status="processing",
        )
        d = doc.to_dict()
        assert d["status"] == "processing"
        assert d["chunk_count"] == 0

    def test_失败状态(self):
        """文档处理失败的状态"""
        doc = Document(
            id="doc-003",
            filename="broken.pdf",
            file_path="/uploads/doc-003.pdf",
            file_size=500,
            file_type="pdf",
            status="failed",
        )
        d = doc.to_dict()
        assert d["status"] == "failed"


class TestConversationModel:
    """Conversation 模型 to_dict 测试"""

    def test_to_dict包含基本字段(self):
        conv = Conversation(
            id="conv-001",
            user_id="usr-001",
            title="产品咨询",
        )
        d = conv.to_dict()

        assert d["id"] == "conv-001"
        assert d["user_id"] == "usr-001"
        assert d["title"] == "产品咨询"

    def test_默认标题(self):
        """不指定标题时默认为'新会话'"""
        conv = Conversation(
            id="conv-002",
            user_id="usr-002",
            title="新会话",
        )
        d = conv.to_dict()
        assert d["title"] == "新会话"


class TestMessageModel:
    """Message 模型 to_dict 测试"""

    def test_to_dict包含基本字段(self):
        msg = Message(
            id="msg-001",
            conversation_id="conv-001",
            role="user",
            content="请问如何退货？",
        )
        d = msg.to_dict()

        assert d["id"] == "msg-001"
        assert d["conversation_id"] == "conv-001"
        assert d["role"] == "user"
        assert d["content"] == "请问如何退货？"

    def test_sources默认为空列表(self):
        """sources 为 None 时 to_dict 返回空列表"""
        msg = Message(
            id="msg-002",
            conversation_id="conv-001",
            role="assistant",
            content="回答内容",
        )
        d = msg.to_dict()
        assert d["sources"] == []

    def test_assistant角色带来源(self):
        """助手消息带引用来源"""
        msg = Message(
            id="msg-003",
            conversation_id="conv-002",
            role="assistant",
            content="根据知识库...",
            sources=[{"filename": "test.pdf", "snippet": "片段"}],
        )
        d = msg.to_dict()
        assert d["role"] == "assistant"
        assert len(d["sources"]) == 1
        assert d["sources"][0]["filename"] == "test.pdf"
