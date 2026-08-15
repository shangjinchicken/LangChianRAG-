"""Embedding 模型封装 —— 使用阿里云百炼 DashScope"""
from langchain_community.embeddings import DashScopeEmbeddings
from app.core import settings


# 全局单例，避免重复初始化
_embedding_model: DashScopeEmbeddings | None = None


def get_embeddings() -> DashScopeEmbeddings:
    """获取 Embedding 模型实例（单例）"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=settings.dashscope_api_key,
        )
    return _embedding_model
