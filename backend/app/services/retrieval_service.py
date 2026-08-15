"""混合检索服务：向量检索 + BM25 关键词检索融合"""
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
import jieba
from app.rag.vector_store import similarity_search_with_score
from cachetools import TTLCache

# 语义缓存：相似问题缓存，TTL=10分钟
semantic_cache: TTLCache = TTLCache(maxsize=200, ttl=600)


def _chinese_tokenize(text: str) -> list[str]:
    """中文分词"""
    return list(jieba.cut(text))


def _bm25_search(query: str, all_chunks: list[Document], top_k: int = 10) -> list[tuple[Document, float]]:
    """
    BM25 关键词检索。
    需要在调用前准备好所有 chunk 的语料库。
    """
    if not all_chunks:
        return []

    # 构建语料库
    corpus = [_chinese_tokenize(doc.page_content) for doc in all_chunks]
    bm25 = BM25Okapi(corpus)

    # 检索
    tokenized_query = _chinese_tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # 归一化分数到 [0, 1]
    max_score = max(scores) if max(scores) > 0 else 1
    normalized = [s / max_score for s in scores]

    # 排序取 top_k
    indexed = list(enumerate(normalized))
    indexed.sort(key=lambda x: x[1], reverse=True)
    top = indexed[:top_k]

    return [(all_chunks[i], score) for i, score in top]


def _rrf_fusion(
    vector_results: list[tuple[Document, float]],
    bm25_results: list[tuple[Document, float]],
    k: int = 60,
) -> list[tuple[Document, float]]:
    """
    Reciprocal Rank Fusion (RRF) 融合向量检索和 BM25 检索结果。
    """
    scores = {}

    # 向量检索结果（按排名给分）
    for rank, (doc, _) in enumerate(vector_results):
        doc_id = doc.page_content[:100]  # 使用前100字符作为近似ID
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

    # BM25 结果
    for rank, (doc, _) in enumerate(bm25_results):
        doc_id = doc.page_content[:100]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)

    # 按分数排序
    all_docs = {doc.page_content[:100]: doc for doc, _ in vector_results + bm25_results}

    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(all_docs[doc_id], score) for doc_id, score in sorted_ids if doc_id in all_docs]


def hybrid_search(query: str, top_k: int = 15) -> list[tuple[Document, float]]:
    """
    混合检索：向量检索 + BM25 融合。
    先从向量库获取全部候选，再用 BM25 重排融合。
    """
    # 1. 向量检索（取多一些候选）
    vector_results = similarity_search_with_score(query, k=top_k * 2)

    # 2. BM25 检索（在所有向量候选中进行关键词匹配）
    all_candidates = [doc for doc, _ in vector_results]
    bm25_results = _bm25_search(query, all_candidates, top_k=top_k)

    # 3. RRF 融合
    fused = _rrf_fusion(vector_results, bm25_results)

    return fused[:top_k]


def get_semantic_cache(query: str) -> str | None:
    """查询语义缓存（基于精确匹配键的前缀）"""
    # 简化实现：使用问题文本的标准化键
    cache_key = query.strip().lower()
    return semantic_cache.get(cache_key)


def set_semantic_cache(query: str, answer: str) -> None:
    """设置语义缓存"""
    cache_key = query.strip().lower()
    semantic_cache[cache_key] = answer
