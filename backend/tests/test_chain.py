"""RAG Chain 单元测试：上下文构建、历史格式化"""
import pytest
from langchain_core.documents import Document
from app.rag.chain import build_context, format_history, RAG_PROMPT


class TestBuildContext:
    """build_context 函数 —— 将检索结果组装为 LLM 可读的上下文"""

    def test_单个文档生成上下文和来源(self):
        """正常流程：一个文档 → 返回一段上下文 + 一条来源"""
        doc = Document(
            page_content="iPhone 15 128GB 售价 5999元",
            metadata={"source": "products.pdf", "page": 0},
        )
        docs_with_scores = [(doc, 0.98)]

        context_text, sources = build_context(docs_with_scores, top_k=5)

        assert isinstance(context_text, str)
        assert "iPhone 15" in context_text
        assert "[1]" in context_text  # 来源编号
        assert len(sources) == 1
        assert sources[0]["filename"] == "products.pdf"
        assert sources[0]["page"] == 1  # page+1 转为人可读页码
        assert len(sources[0]["snippet"]) > 0

    def test_多个文档按分数排序(self):
        """高分文档应排在前面"""
        doc_a = Document(
            page_content="低分内容AAAAA", metadata={"source": "low.pdf"}
        )
        doc_b = Document(
            page_content="高分内容BBBBB", metadata={"source": "high.pdf"}
        )
        docs = [(doc_a, 0.5), (doc_b, 0.99)]

        context_text, sources = build_context(docs, top_k=5)

        # 高分内容应该排在前面 [1]
        assert context_text.index("高分") < context_text.index("低分")
        assert sources[0]["filename"] == "high.pdf"

    def test_top_k截断(self):
        """只取 top_k 条结果"""
        docs = [
            (Document(page_content=f"内容{i}", metadata={"source": f"f{i}.pdf"}), 0.9 - i * 0.1)
            for i in range(10)
        ]
        context_text, sources = build_context(docs, top_k=3)

        assert len(sources) == 3
        # 确认只有 [1] [2] [3] 编号，没有 [4]
        assert "[4]" not in context_text

    def test_空文档列表(self):
        """边界条件：空列表不应崩溃"""
        context_text, sources = build_context([], top_k=5)

        assert context_text == ""
        assert sources == []

    def test_无page字段的文档(self):
        """文档没有 page 元数据时不应显示页码"""
        doc = Document(
            page_content="无页码内容",
            metadata={"source": "manual.txt"},
        )
        docs = [(doc, 0.8)]

        context_text, sources = build_context(docs, top_k=5)

        assert sources[0]["page"] is None
        assert "第" not in context_text.split("[1]")[1].split("\n")[0]

    def test_长文本snippet截断(self):
        """超过 300 字符的 snippet 应截断并加省略号"""
        long_text = "长内容" * 120  # ~480 字符
        doc = Document(page_content=long_text, metadata={"source": "long.txt"})
        docs = [(doc, 0.9)]

        context_text, sources = build_context(docs, top_k=5)

        snippet = sources[0]["snippet"]
        assert len(snippet) <= 303  # 300 + "..."
        assert snippet.endswith("...")

    def test_来源文件名去掉路径前缀(self):
        """Windows 或 Unix 路径只保留文件名"""
        doc = Document(
            page_content="内容",
            metadata={"source": "/home/user/uploads/product.pdf"},
        )
        docs = [(doc, 0.95)]

        _, sources = build_context(docs, top_k=5)

        assert sources[0]["filename"] == "product.pdf"
        assert "/" not in sources[0]["filename"]


class TestFormatHistory:
    """format_history 函数 —— 将对话历史格式化为 LLM 可读文本"""

    def test_空历史返回提示文本(self):
        """无历史对话时返回友好提示"""
        result = format_history([])
        assert "无历史对话" in result

    def test_None历史同空历史处理(self):
        """None 等同于空历史"""
        result = format_history(None)  # type: ignore
        assert "无历史对话" in result

    def test_单轮对话格式化(self):
        """一问一答"""
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的？"},
        ]
        result = format_history(history)

        assert "用户" in result
        assert "助手" in result
        assert "你好" in result

    def test_超过6条只取最近6条(self):
        """只保留最近 6 条消息避免上下文过长"""
        history = [
            {"role": "user", "content": f"消息{i}"}
            for i in range(10)
        ]
        result = format_history(history)

        # 最近 6 条：消息4-消息9
        assert "消息4" in result
        assert "消息9" in result
        # 旧消息不在
        assert "消息0" not in result
        assert "消息3" not in result
        # 应只有 6 行
        assert result.count("\n") == 5  # 6 条消息 = 5 个换行

    def test_多条对话格式正确(self):
        """格式化后每条消息独立一行"""
        history = [
            {"role": "user", "content": "问题1"},
            {"role": "assistant", "content": "回答1"},
            {"role": "user", "content": "问题2"},
            {"role": "assistant", "content": "回答2"},
        ]
        result = format_history(history)

        lines = result.split("\n")
        assert len(lines) == 4
        assert lines[0].startswith("用户: ")
        assert lines[1].startswith("助手: ")


class TestRAGPrompt:
    """RAG 提示词模板"""

    def test_模板包含必要占位符(self):
        """模板必须包含 context, history, question 三个占位符"""
        system_template = RAG_PROMPT.messages[0].prompt.template
        assert "{context}" in system_template
        assert "{history}" in system_template
        assert "{question}" in str(RAG_PROMPT.messages)

    def test_模板可正确填充(self):
        """通过 format 填充模板不报错"""
        system_template = RAG_PROMPT.messages[0].prompt.template
        filled = system_template.format(
            context="[1] 来源: test.pdf\n测试内容",
            history="用户: 你好\n助手: 你好！",
        )
        assert "test.pdf" in filled
        assert "你好" in filled
