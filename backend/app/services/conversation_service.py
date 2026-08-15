"""会话服务：CRUD + 消息管理"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User


def list_conversations(db: Session, user: User) -> list[dict]:
    """获取用户的所有会话列表，按最后更新时间倒序"""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    result = []
    for conv in conversations:
        msg_count = (
            db.query(Message).filter(Message.conversation_id == conv.id).count()
        )
        d = conv.to_dict()
        d["message_count"] = msg_count
        result.append(d)
    return result


def create_conversation(db: Session, user: User, title: str = "新会话") -> Conversation:
    """创建新会话"""
    conv = Conversation(user_id=user.id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def update_conversation_title(db: Session, user: User, conv_id: str, title: str) -> Conversation:
    """更新会话标题"""
    conv = _get_user_conversation(db, user, conv_id)
    conv.title = title
    db.commit()
    db.refresh(conv)
    return conv


def delete_conversation(db: Session, user: User, conv_id: str) -> None:
    """删除会话及其所有消息"""
    conv = _get_user_conversation(db, user, conv_id)
    db.delete(conv)
    db.commit()


def get_messages(db: Session, user: User, conv_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    """获取会话的消息列表（分页）"""
    _get_user_conversation(db, user, conv_id)  # 验证权限
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [m.to_dict() for m in messages]


def add_message(db: Session, conv_id: str, role: str, content: str, sources: list | None = None) -> Message:
    """添加一条消息到会话"""
    msg = Message(
        conversation_id=conv_id,
        role=role,
        content=content,
        sources=sources or [],
    )
    db.add(msg)
    # 更新会话最后活跃时间
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if conv:
        from datetime import datetime
        conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


def get_conversation_context(db: Session, conv_id: str, max_messages: int = 10) -> list[dict]:
    """获取最近 N 条消息作为对话上下文"""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.desc())
        .limit(max_messages)
        .all()
    )
    return [
        {"role": m.role, "content": m.content}
        for m in reversed(messages)
    ]


def _get_user_conversation(db: Session, user: User, conv_id: str) -> Conversation:
    """获取会话并验证属于当前用户"""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    if conv.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此会话")
    return conv
