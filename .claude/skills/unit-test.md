---
name: unit-test
description: 为项目代码创建单元测试、执行测试、生成测试报告
model: sonnet
---

# 单元测试技能

## 技能说明

本技能用于为「RAG 企业级知识库问答系统」项目创建、执行单元测试，并生成测试报告。

**测试框架**：pytest + pytest-asyncio + pytest-cov
**测试环境**：Python 3.14，虚拟环境 `backend/venv/`

---

## 执行流程

### 第一步：分析测试目标

1. 询问用户想测试哪个模块/文件/函数：
   - **RAG 核心层**（`backend/app/rag/*.py`）：splitter、chain、embeddings、loaders
   - **安全层**（`backend/app/core/security.py`）：密码哈希、JWT 令牌
   - **数据模型层**（`backend/app/models/*.py`）：ORM 模型 `to_dict()` 方法
   - **数据校验层**（`backend/app/schemas/*.py`）：Pydantic 模型验证规则
   - **服务层**（`backend/app/services/*.py`）：业务逻辑（需要 mock 数据库）
2. 读取目标文件，理解其功能、输入输出、边界条件，然后直接创建单元测试。

### 第二步：创建测试文件

1. 测试文件放在 `backend/tests/` 目录下
2. 命名规则：`test_模块名.py`（例如 `test_security.py`、`test_splitter.py`）
3. 测试文件结构遵循 AAA 模式：
   - **Arrange**（准备）：准备好测试数据和环境
   - **Act**（执行）：调用被测函数
   - **Assert**（断言）：验证结果是否符合预期

#### 纯函数测试模板

```python
import pytest
from app.rag.chain import build_context, format_history

class TestBuildContext:
    """build_context 函数单元测试"""

    def test_正常输入返回上下文文本和来源列表(self):
        # Arrange — 准备
        from langchain_core.documents import Document
        doc = Document(page_content="测试内容", metadata={"source": "test.pdf"})
        docs_with_scores = [(doc, 0.95)]

        # Act — 执行
        context_text, sources = build_context(docs_with_scores, top_k=5)

        # Assert — 断言
        assert isinstance(context_text, str)
        assert len(sources) == 1
        assert "测试内容" in context_text
```

#### Pydantic 验证测试模板

```python
import pytest
from app.schemas.auth import RegisterRequest, LoginRequest

class TestRegisterRequest:
    """注册请求校验单元测试"""

    def test_用户名过短应报错(self):
        with pytest.raises(Exception):
            RegisterRequest(username="a", password="123456")

    def test_正常输入通过校验(self):
        req = RegisterRequest(username="testuser", password="123456")
        assert req.username == "testuser"
```

### 第三步：执行测试

1. 写完测试文件后，进入 `backend/` 目录运行：

```bash
# 激活虚拟环境（Git Bash）
source venv/Scripts/activate

# 运行全部测试
pytest tests/ -v
```

2. 如果需要查看覆盖率报告：

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### 第四步：生成测试报告

测试跑完后，向用户用中文报告以下内容：

```
📊 单元测试报告
═══════════════════════════

📁 测试文件：X 个
🧪 测试用例：Y 个
✅ 通过：A 个
❌ 失败：B 个
⏱️  总耗时：Z s

📋 详细结果：
  ✅ 测试名称1
  ✅ 测试名称2
  ❌ 测试名称3 — 失败原因：预期值是 X，实际值是 Y

📌 建议：
  - 如果全部通过：代码质量良好，本次改动没有破坏已有功能
  - 如果有失败：请检查上述失败用例，修复对应代码后重新测试
```

### 第五步：修复建议

如果有测试失败，分析失败原因并给出修复建议。如果用户要求，直接帮忙修复代码。

---

## 注意事项

### 技术约束
- 项目使用 SQLite 数据库，测试中应使用 mock 或内存数据库避免影响真实数据
- ChromaDB 向量库在测试中需要 mock，避免需要真实 embedding
- 测试不应调用阿里云百炼真实 API（产生费用），需要 mock LLM 和 Embedding
- 异步函数测试需要用 `pytest-asyncio` 的 `@pytest.mark.asyncio` 标记

### 沟通规范
- 用通俗语言解释每个测试用例在测什么、为什么测这个
- 测试报告必须用中文

### 项目特定说明
- 被测代码位于 `backend/app/` 目录下
- `app.core.settings` 的 `.env` 文件中有阿里云 API Key，测试不应依赖真实 API
- 运行测试前需激活 `backend/venv/` 虚拟环境
- 项目使用 Python 3.14

---

## 快速参考命令

| 命令 | 作用 |
|------|------|
| `pytest tests/ -v` | 运行全部测试（详细输出） |
| `pytest tests/ -v -s` | 运行测试并显示 print 输出 |
| `pytest tests/test_security.py -v` | 只运行某个测试文件 |
| `pytest tests/ -v -k "test_密码"` | 按关键字过滤运行 |
| `pytest tests/ -v --cov=app --cov-report=term-missing` | 运行测试并查看覆盖率 |
| `pytest tests/ -v --tb=short` | 简化错误输出 |
