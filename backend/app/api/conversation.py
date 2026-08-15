"""会话管理 API：CRUD + 消息历史"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse, MessageResponse
from app.services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["会话"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户的会话列表"""
    return conversation_service.list_conversations(db, current_user)


@router.post("", response_model=ConversationResponse)
def create_conversation(
    req: ConversationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新会话"""
    conv = conversation_service.create_conversation(db, current_user, req.title)
    d = conv.to_dict()
    d["message_count"] = 0
    return d


@router.patch("/{conv_id}", response_model=ConversationResponse)
def update_conversation(
    conv_id: str,
    req: ConversationUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """重命名会话"""
    conv = conversation_service.update_conversation_title(db, current_user, conv_id, req.title)
    d = conv.to_dict()
    d["message_count"] = 0
    return d


@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除会话"""
    conversation_service.delete_conversation(db, current_user, conv_id)
    return {"message": "会话已删除"}


@router.get("/{conv_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conv_id: str,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话的消息历史（分页）"""
    return conversation_service.get_messages(db, current_user, conv_id, limit, offset)
