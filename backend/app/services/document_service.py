"""文档管理服务：上传、处理、删除"""
import os
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from app.core import settings
from app.models.document import Document
from app.rag.loaders import load_document
from app.rag.splitter import split_documents
from app.rag.vector_store import add_documents, delete_by_document_id


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".xls", ".txt", ".md", ".csv"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def upload_and_process(db: Session, file: UploadFile) -> Document:
    """上传文件并进行向量化处理"""
    # 验证文件类型
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}。支持: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 读取并保存文件
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件大小不能超过 20MB")

    file_id = str(uuid.uuid4())
    save_name = f"{file_id}{ext}"
    save_path = os.path.join(settings.upload_dir, save_name)
    with open(save_path, "wb") as f:
        f.write(content)

    file_size = len(content)

    # 创建数据库记录（状态：processing）
    doc = Document(
        id=file_id,
        filename=file.filename,
        file_path=save_path,
        file_size=file_size,
        file_type=ext.lstrip("."),
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 执行向量化处理
    try:
        _process_document(db, doc)
    except Exception as e:
        doc.status = "failed"
        db.commit()
        # 清理已入库的部分向量
        try:
            delete_by_document_id(doc.id)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}",
        )

    return doc


def _process_document(db: Session, doc: Document) -> None:
    """对文档进行加载、分割、向量化"""
    # 1. 加载文档
    raw_docs = load_document(doc.file_path)

    # 2. 为每个文档添加 doc_id 元数据，便于后续删除
    for d in raw_docs:
        d.metadata["doc_id"] = doc.id
        d.metadata["filename"] = doc.filename

    # 3. 分割
    chunks = split_documents(raw_docs)

    # 4. 向量化并入库
    add_documents(chunks)

    # 5. 更新状态
    doc.chunk_count = len(chunks)
    doc.status = "completed"
    db.commit()


def list_documents(db: Session, page: int = 1, page_size: int = 20) -> dict:
    """分页查询文档列表"""
    total = db.query(Document).count()
    items = (
        db.query(Document)
        .order_by(Document.uploaded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "items": [item.to_dict() for item in items],
    }


def delete_document(db: Session, doc_id: str) -> None:
    """删除文档及其向量数据"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    # 1. 删除向量数据
    try:
        delete_by_document_id(doc_id)
    except Exception:
        pass  # 向量删除失败不阻塞数据库删除

    # 2. 删除物理文件
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # 3. 删除数据库记录
    db.delete(doc)
    db.commit()


def get_stats(db: Session) -> dict:
    """获取知识库统计"""
    from app.rag.vector_store import get_collection_stats

    total_docs = db.query(Document).filter(Document.status == "completed").count()
    total_size = db.query(Document).with_entities(Document.file_size).filter(Document.status == "completed").all()
    total_size_sum = sum(r[0] for r in total_size)
    vector_stats = get_collection_stats()

    return {
        "document_count": total_docs,
        "total_chunks": vector_stats.get("total_chunks", 0),
        "total_size": total_size_sum,
    }
