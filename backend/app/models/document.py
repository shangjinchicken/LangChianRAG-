"""知识库文档模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    file_type = Column(String(20), nullable=False, default="unknown")
    chunk_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pending")  # pending/processing/completed/failed
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
