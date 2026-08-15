"""文本分割器 —— 针对中文优化的递归字符分割"""
from langchain.text_splitter import RecursiveCharacterTextSplitter


def get_text_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> RecursiveCharacterTextSplitter:
    """
    创建针对中文优化的文本分割器。
    使用中文标点和常见分隔符作为分割优先级。
    """
    separators = [
        "\n\n",     # 段落
        "\n",       # 换行
        "。",       # 中文句号
        "！",       # 中文感叹号
        "？",       # 中文问号
        "；",       # 中文分号
        "，",       # 中文逗号
        ".",        # 英文句号
        " ",        # 空格
        "",         # 字符级
    ]
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        keep_separator=True,  # 保留分隔符，保持语义完整
    )


def split_documents(documents: list, chunk_size: int = 500, chunk_overlap: int = 50) -> list:
    """
    将文档列表分割为文本块。
    每个块保留原始元数据，并添加 chunk_index。
    """
    splitter = get_text_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_documents(documents)

    # 为每个 chunk 添加序号
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i

    return chunks
