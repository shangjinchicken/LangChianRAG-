"""文档加载器工厂 —— 根据文件类型选择合适的 LangChain Loader"""
import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
)
from langchain_core.documents import Document


def _load_excel(file_path: str) -> list[Document]:
    """使用 openpyxl 加载 Excel 文件（避免 heavy unstructured 依赖）"""
    import openpyxl
    docs = []
    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            # 过滤全空行
            if any(cell is not None for cell in row):
                row_text = " | ".join(str(cell) if cell is not None else "" for cell in row)
                rows.append(row_text)
        if rows:
            text = "\n".join(rows)
            docs.append(Document(
                page_content=text,
                metadata={"source": file_path, "sheet": sheet_name}
            ))
    wb.close()
    return docs


def load_document(file_path: str) -> list[Document]:
    """
    根据文件扩展名自动选择加载器，返回 LangChain Document 列表。
    每个 Document 包含 page_content 和 metadata。
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext in (".xlsx", ".xls"):
        return _load_excel(file_path)
    elif ext in (".txt", ".md"):
        loader = TextLoader(file_path, encoding="utf-8")
    elif ext == ".csv":
        loader = CSVLoader(file_path, encoding="utf-8")
    else:
        supported = ".pdf, .docx, .xlsx, .xls, .txt, .md, .csv"
        raise ValueError(f"不支持的文件类型: {ext}。支持的格式: {supported}")

    return loader.load()
