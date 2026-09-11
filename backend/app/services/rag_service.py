"""RAG 问答服务：检索 + 生成 + 流式输出"""
import asyncio
import json
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, SystemMessage
from app.rag.chain import get_llm, build_context, format_history, RAG_PROMPT
from app.services.retrieval_service import hybrid_search, get_semantic_cache, set_semantic_cache


async def generate_answer_stream(
    question: str,
    history: list[dict],
    use_cache: bool = True,
) -> AsyncGenerator[str, None]:
    """
    RAG 流式问答。
    1. 检查语义缓存
    2. 混合检索获取相关知识
    3. 构建上下文
    4. 流式生成回答
    """

    # === 第1步：检查语义缓存 ===
    if use_cache:
        cached = get_semantic_cache(question)
        if cached:
            # 直接返回缓存结果（也以流式方式输出）
            yield f"data: {json.dumps({'type': 'cached', 'content': '', 'sources': []})}\n\n"
            for char in cached:
                yield f"data: {json.dumps({'type': 'token', 'content': char, 'sources': []})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'content': '', 'sources': []})}\n\n"
            return

    # === 第2步：混合检索（同步阻塞：Chroma 查询 + jieba 分词 + BM25，丢线程池避免卡事件循环）===
    try:
        docs_with_scores = await asyncio.to_thread(hybrid_search, question, 15)
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': f'检索失败: {str(e)}', 'sources': []})}\n\n"
        return

    # === 第3步：构建上下文 ===
    context_text, sources = build_context(docs_with_scores, top_k=5)

    # === 第4步：发送引用来源 ===
    yield f"data: {json.dumps({'type': 'sources', 'content': '', 'sources': sources})}\n\n"

    # === 第5步：构建 Prompt ===
    history_text = format_history(history)

    system_prompt = RAG_PROMPT.messages[0].prompt.template.format(
        context=context_text,
        history=history_text,
    )
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]

    # === 第6步：流式生成 ===
    llm = get_llm(streaming=True)
    full_answer = ""

    try:
        async for chunk in llm.astream(input=messages):
            # Tongyi(BaseLLM) astream yields raw strings directly
            # Compatible with both BaseLLM (string) and BaseChatModel (.content attribute)
            if isinstance(chunk, str):
                content = chunk
            elif hasattr(chunk, "content") and chunk.content:
                content = chunk.content
            else:
                continue

            if isinstance(content, str) and content:
                full_answer += content
                yield f"data: {json.dumps({'type': 'token', 'content': content, 'sources': []})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': f'生成回答失败: {str(e)}', 'sources': sources})}\n\n"
        return

    # === 第7步：缓存结果 ===
    if use_cache and full_answer:
        set_semantic_cache(question, full_answer)

    # === 第8步：结束信号 ===
    yield f"data: {json.dumps({'type': 'done', 'content': '', 'sources': sources})}\n\n"
