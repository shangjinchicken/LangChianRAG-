"""ChromaDB 向量存储操作封装"""
import os
import chromadb
from langchain_community.vectorstores import Chroma
from app.core import settings
from app.rag.embeddings import get_embeddings

# ChromaDB 持久化客户端（全局单例）
_client: chromadb.PersistentClient | None = None
_vector_store: Chroma | None = None

COLLECTION_NAME = "knowledge_base"


def _get_client() -> chromadb.PersistentClient:
    """获取 ChromaDB 持久化客户端"""
    global _client
    if _client is None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_vector_store() -> Chroma:
    """获取向量存储实例"""
    global _vector_store
    if _vector_store is None:
        embeddings = get_embeddings()
        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            client=_get_client(),
        )
    return _vector_store


def add_documents(chunks: list) -> None:
    """将文档块添加到向量库"""
    if not chunks:
        return
    store = get_vector_store()
    store.add_documents(chunks)


def delete_by_document_id(doc_id: str) -> None:
    """根据文档 ID 删除向量（通过 metadata 中的 doc_id 过滤）"""
    store = get_vector_store()
    # ChromaDB 通过 metadata 过滤删除
    collection = store._collection
    results = collection.get(where={"doc_id": doc_id})
    ids_to_delete = results.get("ids", [])
    if ids_to_delete:
        collection.delete(ids=ids_to_delete)


def similarity_search(query: str, k: int = 15) -> list:
    """向量相似度检索，返回最相关的 k 个文档块"""
    store = get_vector_store()
    return store.similarity_search(query, k=k)


def similarity_search_with_score(query: str, k: int = 15) -> list[tuple]:
    """向量相似度检索（带分数），返回 (document, score) 元组列表"""
    store = get_vector_store()
    return store.similarity_search_with_relevance_scores(query, k=k)


def get_collection_stats() -> dict:
    """获取向量库统计信息"""
    try:
        store = get_vector_store()
        collection = store._collection
        count = collection.count()
        return {"total_chunks": count}
    except Exception:
        return {"total_chunks": 0}
