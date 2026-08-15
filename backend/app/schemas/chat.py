"""问答相关 Pydantic 模型"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户问题")


class SourceInfo(BaseModel):
    filename: str
    snippet: str
    page: int | None = None
    chunk_index: int | None = None


class ChatStreamChunk(BaseModel):
    """SSE 流式响应的每个 chunk"""
    type: str  # "token" | "sources" | "done" | "error"
    content: str = ""
    sources: list[SourceInfo] = []
