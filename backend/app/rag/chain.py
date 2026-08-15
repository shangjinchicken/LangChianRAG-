"""RAG Chain 组装 —— 检索 + 生成"""
from langchain_community.llms import Tongyi
from langchain_core.prompts import ChatPromptTemplate
from app.core import settings
from app.rag.vector_store import similarity_search_with_score


# RAG 提示词模板
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的电商客服助手，专门回答用户关于商品的问题。
你需要严格根据以下【知识库内容】来回答用户问题。

规则：
1. 优先使用知识库中的信息回答，不要编造不存在的信息
2. 如果知识库中没有相关信息，请诚实地说"根据现有知识库，我暂时无法回答这个问题"
3. 回答时使用 [N] 标注引用了第几条知识库内容
4. 回答要简洁清晰，适合电商场景
5. 如果涉及价格、库存等时效性信息，提醒用户以实际页面为准

【知识库内容】：
{context}

【对话历史】：
{history}"""),
    ("human", "{question}"),
])


def get_llm(streaming: bool = True) -> Tongyi:
    """获取 LLM 实例"""
    return Tongyi(
        model="qwen-plus",
        dashscope_api_key=settings.dashscope_api_key,
        streaming=streaming,
        temperature=0.3,  # 低温度，减少幻觉
        top_p=0.8,
    )


def build_context(docs_with_scores: list[tuple], top_k: int = 5) -> tuple[str, list[dict]]:
    """
    构建 LLM 上下文和引用来源列表。
    返回 (context_text, sources_list)
    """
    sources = []
    context_parts = []

    # 按分数降序排列，取 top_k
    sorted_docs = sorted(docs_with_scores, key=lambda x: x[1], reverse=True)[:top_k]

    for i, (doc, score) in enumerate(sorted_docs, 1):
        filename = doc.metadata.get("source", "未知文件")
        page = doc.metadata.get("page")
        chunk_idx = doc.metadata.get("chunk_index")

        context_parts.append(f"[{i}] 来源: {filename}" + (f" (第{page+1}页)" if page is not None else "") + f"\n{doc.page_content}")

        sources.append({
            "filename": filename.split("/")[-1] if "/" in filename else filename.split("\\")[-1],
            "snippet": doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else ""),
            "page": page + 1 if page is not None else None,
            "chunk_index": chunk_idx,
        })

    return "\n\n".join(context_parts), sources


def format_history(history: list[dict]) -> str:
    """将对话历史格式化为文本"""
    if not history:
        return "（无历史对话）"
    parts = []
    for msg in history[-6:]:  # 最多取最近 6 条
        role = "用户" if msg["role"] == "user" else "助手"
        parts.append(f"{role}: {msg['content']}")
    return "\n".join(parts)
