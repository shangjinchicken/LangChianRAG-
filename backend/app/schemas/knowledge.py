"""知识库管理相关 Pydantic 模型"""
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    file_type: str
    chunk_count: int
    status: str
    uploaded_at: str | None = None


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]


class KnowledgeStatsResponse(BaseModel):
    document_count: int
    total_chunks: int
    total_size: int
