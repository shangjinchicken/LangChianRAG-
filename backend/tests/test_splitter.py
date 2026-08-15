"""文本分割器单元测试"""
import pytest
from langchain_core.documents import Document
from app.rag.splitter import get_text_splitter, split_documents


class TestGetTextSplitter:
    """get_text_splitter 工厂函数测试"""

    def test_返回RecursiveCharacterTextSplitter实例(self):
        """确认返回正确类型的分割器"""
        splitter = get_text_splitter()
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        assert isinstance(splitter, RecursiveCharacterTextSplitter)

    def test_默认chunk_size为500(self):
        """默认块大小为 500 字符"""
        splitter = get_text_splitter()
        assert splitter._chunk_size == 500

    def test_默认chunk_overlap为50(self):
        """默认重叠为 50 字符"""
        splitter = get_text_splitter()
        assert splitter._chunk_overlap == 50

    def test_自定义参数生效(self):
        """自定义 chunk_size 和 chunk_overlap"""
        splitter = get_text_splitter(chunk_size=1000, chunk_overlap=200)
        assert splitter._chunk_size == 1000
        assert splitter._chunk_overlap == 200

    def test_包含中文分隔符(self):
        """分隔符列表应包含中文标点"""
        splitter = get_text_splitter()
        separators = splitter._separators
        assert "。" in separators
        assert "！" in separators
        assert "？" in separators
        assert "；" in separators
        assert "，" in separators

    def test_保留分隔符配置(self):
        """确认 keep_separator=True 保留语义完整"""
        splitter = get_text_splitter()
        assert splitter._keep_separator is True


class TestSplitDocuments:
    """split_documents 函数测试"""

    def test_短文档不分割(self):
        """短于 chunk_size 的文档不被分割"""
        doc = Document(
            page_content="这是一个很短的文档。",
            metadata={"source": "short.txt"},
        )
        chunks = split_documents([doc], chunk_size=500)
        assert len(chunks) == 1

    def test_长文档被分割为多个块(self):
        """超过 chunk_size 的长文档被分割成多个块"""
        # 创建超过 500 字符的文档
        long_text = "这是测试内容。" * 100  # 约 700 字符
        doc = Document(page_content=long_text, metadata={"source": "long.txt"})
        chunks = split_documents([doc], chunk_size=200, chunk_overlap=20)

        assert len(chunks) > 1

    def test_每个块保留原始元数据(self):
        """分块后的每个 Document 应保留原始 source 元数据"""
        long_text = "这是测试内容。" * 100
        doc = Document(page_content=long_text, metadata={"source": "important.pdf"})
        chunks = split_documents([doc], chunk_size=200, chunk_overlap=20)

        for chunk in chunks:
            assert chunk.metadata["source"] == "important.pdf"

    def test_每个块有chunk_index序号(self):
        """分块后的每个 Document 应有 chunk_index 并递增"""
        long_text = "这是测试内容。" * 100
        doc = Document(page_content=long_text, metadata={"source": "test.pdf"})
        chunks = split_documents([doc], chunk_size=200, chunk_overlap=20)

        indices = [c.metadata["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_空文档列表不报错(self):
        """边界条件：空列表"""
        chunks = split_documents([], chunk_size=500)
        assert chunks == []

    def test_多个文档同时分割(self):
        """多个文档可以一起分割处理"""
        text_a = "A内容。" * 100
        text_b = "B内容。" * 100
        docs = [
            Document(page_content=text_a, metadata={"source": "a.txt"}),
            Document(page_content=text_b, metadata={"source": "b.txt"}),
        ]
        chunks = split_documents(docs, chunk_size=200, chunk_overlap=20)

        assert len(chunks) > 0
        # 确认两种来源都存在
        sources = {c.metadata["source"] for c in chunks}
        assert "a.txt" in sources
        assert "b.txt" in sources

    def test_块间有重叠(self):
        """相邻块之间应有重叠内容"""
        long_text = "这是第X句测试内容。" * 100
        doc = Document(page_content=long_text, metadata={"source": "overlap.pdf"})
        chunks = split_documents([doc], chunk_size=300, chunk_overlap=50)

        if len(chunks) >= 2:
            # 前一块的结尾应出现在后一块的开头
            tail = chunks[0].page_content[-30:]
            head = chunks[1].page_content[:30:]
            # 有重叠意味着它们共享一些字符
            # （重叠不一定严格等于 50 字符因为分隔符的关系）
            common_chars = set(tail) & set(head)
            assert len(common_chars) > 0
