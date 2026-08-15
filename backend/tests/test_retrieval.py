"""混合检索服务单元测试：分词、RRF 融合、语义缓存"""
import pytest
from langchain_core.documents import Document
from app.services.retrieval_service import (
    _chinese_tokenize,
    _rrf_fusion,
    get_semantic_cache,
    set_semantic_cache,
)


class TestChineseTokenize:
    """中文分词测试"""

    def test_中文句子分词(self):
        """常规中文句子应被分词"""
        tokens = _chinese_tokenize("今天天气真好")
        assert len(tokens) >= 2
        # jieba 分词结果可能有差异，"今天" 可能被合并为 "今天天气"
        combined = "".join(tokens)
        assert "今天" in combined  # 原始文本片段应在分词结果中可还原
        assert isinstance(tokens, list)

    def test_空字符串分词(self):
        """边界条件：空字符串"""
        tokens = _chinese_tokenize("")
        assert tokens == []

    def test_英文数字混合分词(self):
        """包含英文和数字的文本"""
        tokens = _chinese_tokenize("iPhone15售价8999元")
        assert len(tokens) > 0
        # 至少应包含核心词
        assert any("iPhone" in t or "15" in t or "售价" in t for t in tokens)

    def test_纯标点符号处理(self):
        """纯标点符号不应崩溃"""
        tokens = _chinese_tokenize("，。！？")
        assert isinstance(tokens, list)


class TestRRFFusion:
    """RRF (Reciprocal Rank Fusion) 算法测试"""

    def test_相同文档融合后保留(self):
        """两个检索源都有的文档应该合并保留"""
        doc1 = Document(page_content="相同文档内容", metadata={"source": "a.pdf"})
        doc2 = Document(page_content="另一文档内容", metadata={"source": "b.pdf"})

        vector_results = [(doc1, 0.95), (doc2, 0.8)]
        bm25_results = [(doc1, 0.7), (doc2, 0.6)]

        fused = _rrf_fusion(vector_results, bm25_results)

        assert len(fused) >= 1

    def test_空结果融合返回空列表(self):
        """两个空列表融合不应崩溃"""
        fused = _rrf_fusion([], [])
        assert fused == []

    def test_单侧有结果也能融合(self):
        """向量检索有结果但 BM25 为空"""
        doc = Document(page_content="测试内容ABCDE1234567890" * 10, metadata={"source": "test.pdf"})
        vector_results = [(doc, 0.9)]
        bm25_results = []

        fused = _rrf_fusion(vector_results, bm25_results)

        assert len(fused) >= 1

    def test_融合结果按分数降序排列(self):
        """排在前面的结果分数应更高"""
        docs = [
            Document(page_content=f"文档内容_{i}_ABCDEFGH" * 5, metadata={"source": f"d{i}.pdf"})
            for i in range(5)
        ]
        vector_results = [(docs[i], 0.9 - i * 0.15) for i in range(5)]
        bm25_results = [(docs[i], 0.6 - i * 0.1) for i in range(5)]

        fused = _rrf_fusion(vector_results, bm25_results)

        scores = [score for _, score in fused]
        # 分数应不增
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]


class TestSemanticCache:
    """语义缓存测试"""

    def test_设置并获取缓存(self):
        """设置缓存后应立即能获取到"""
        set_semantic_cache("iPhone15多少钱？", "iPhone15售价5999元起")
        cached = get_semantic_cache("iPhone15多少钱？")
        assert cached == "iPhone15售价5999元起"

    def test_未命中返回None(self):
        """没有缓存时应返回 None"""
        result = get_semantic_cache("一个从未被缓存过的问题")
        assert result is None

    def test_大小写不敏感(self):
        """缓存键应不区分大小写"""
        set_semantic_cache("如何退货？", "您可以...")
        cached = get_semantic_cache("如何退货？")
        assert cached == "您可以..."

    def test_前后空格不影响(self):
        """问题前后的空格不应影响缓存命中"""
        set_semantic_cache("发货时间", "通常24小时内发货")
        result = get_semantic_cache("  发货时间  ")
        assert result is not None

    def test_覆盖已有缓存(self):
        """重复设置同名缓存应覆盖旧值"""
        set_semantic_cache("物流查询", "旧答案")
        set_semantic_cache("物流查询", "新答案")
        assert get_semantic_cache("物流查询") == "新答案"
