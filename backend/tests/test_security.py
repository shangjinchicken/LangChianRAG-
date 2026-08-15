"""安全模块单元测试：密码哈希、JWT 令牌"""
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestHashPassword:
    """密码哈希功能测试"""

    def test_哈希值和原文不同(self):
        """密码原文不被直接存储，哈希后应完全不同"""
        hashed = hash_password("123456")
        assert hashed != "123456"

    def test_相同密码两次哈希产生不同结果(self):
        """bcrypt 每次加盐不同，两次哈希应不同"""
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2

    def test_空密码不报错(self):
        """边界条件：空字符串密码"""
        hashed = hash_password("")
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestVerifyPassword:
    """密码验证功能测试"""

    def test_正确密码验证通过(self):
        """正常流程：输入正确密码应返回 True"""
        hashed = hash_password("admin123")
        assert verify_password("admin123", hashed) is True

    def test_错误密码验证不通过(self):
        """安全要求：输错密码应返回 False"""
        hashed = hash_password("admin123")
        assert verify_password("wrongpassword", hashed) is False

    def test_大小写敏感(self):
        """密码验证应区分大小写"""
        hashed = hash_password("Password")
        assert verify_password("password", hashed) is False

    def test_含特殊字符的密码(self):
        """边界条件：包含特殊字符的密码"""
        pwd = "P@ssw0rd!#$%^&*()中文字符"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True


class TestJWT:
    """JWT 令牌生成和解析测试"""

    def test_生成令牌返回非空字符串(self):
        """正常流程：create_access_token 返回三段式 JWT"""
        token = create_access_token("user-123", "testuser", "user")
        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT 格式：header.payload.signature

    def test_解析有效令牌返回正确载荷(self):
        """正常流程：decode 能获取原始信息"""
        token = create_access_token("user-456", "alice", "admin")
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["username"] == "alice"
        assert payload["role"] == "admin"

    def test_解析伪造令牌返回None(self):
        """安全要求：伪造成的 JWT 应被拒绝"""
        payload = decode_access_token("not.a.real.token.at.all")
        assert payload is None

    def test_解析空字符串返回None(self):
        """边界条件：空 token"""
        payload = decode_access_token("")
        assert payload is None

    def test_令牌包含过期时间(self):
        """JWT 应包含 exp 过期时间字段"""
        token = create_access_token("user-789", "bob", "user")
        payload = decode_access_token(token)
        assert payload is not None
        assert "exp" in payload
        assert isinstance(payload["exp"], int)
