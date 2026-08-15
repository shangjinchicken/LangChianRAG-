"""消息模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(10), nullable=False)  # 'user' 或 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # 引用来源列表 [{"filename":"...","snippet":"...","page":...}]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
