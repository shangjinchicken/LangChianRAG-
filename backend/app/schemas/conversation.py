"""会话相关 Pydantic 模型"""
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="新会话", max_length=200, description="会话标题")


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="新标题")


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None
    message_count: int = 0  # 消息数量


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list = []
    created_at: str | None = None
