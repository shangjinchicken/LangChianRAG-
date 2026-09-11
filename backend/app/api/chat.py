"""问答 API：SSE 流式聊天 + 消息持久化"""
import asyncio
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, get_db
from app.core.security import get_current_user
from app.schemas.chat import ChatRequest
from app.services import rag_service, conversation_service

router = APIRouter(prefix="/api/conversations", tags=["问答"])


@router.post("/{conv_id}/chat")
async def chat(
    conv_id: str,
    req: ChatRequest,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发送消息并进行 RAG 问答（SSE 流式返回）"""
    # 1. 验证会话权限 + 获取对话历史（同步 DB 操作丢线程池，避免阻塞事件循环）
    history = await asyncio.to_thread(
        conversation_service.get_conversation_context, db, conv_id
    )

    # 2. 存储用户消息
    await asyncio.to_thread(
        conversation_service.add_message, db, conv_id, "user", req.message
    )

    # 前置 DB 操作已完成，立即释放连接——不要在流式期间（可能几十秒）占用连接池
    db.close()

    # 3. 准备 SSE 流式响应
    async def event_stream():
        collected_sources = []
        full_answer = ""

        try:
            async for sse_chunk in rag_service.generate_answer_stream(
                question=req.message,
                history=history,
            ):
                # 检查客户端是否断开连接
                if await request.is_disconnected():
                    break
                yield sse_chunk

                # 收集来源和答案
                try:
                    data = json.loads(sse_chunk.replace("data: ", "").strip())
                    if data.get("type") == "sources":
                        collected_sources = data.get("sources", [])
                    elif data.get("type") == "token":
                        full_answer += data.get("content", "")
                except (json.JSONDecodeError, AttributeError):
                    pass

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e), 'sources': []})}\n\n"

        finally:
            # 4. 存储助手消息（完整回答）——用新的短生命周期 session，用完即关
            if full_answer:
                assistant_db = SessionLocal()
                try:
                    await asyncio.to_thread(
                        conversation_service.add_message,
                        assistant_db,
                        conv_id,
                        "assistant",
                        full_answer,
                        collected_sources,
                    )
                finally:
                    assistant_db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
