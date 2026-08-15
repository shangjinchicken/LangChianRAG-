"""知识库管理 API（仅管理员可访问）"""
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.schemas.knowledge import DocumentResponse, DocumentListResponse, KnowledgeStatsResponse
from app.services import document_service

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取知识库文档列表（分页）"""
    return document_service.list_documents(db, page, page_size)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """上传文档并自动向量化"""
    doc = document_service.upload_and_process(db, file)
    return doc.to_dict()


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: str,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """删除文档及其向量数据"""
    document_service.delete_document(db, doc_id)
    return {"message": "文档已删除"}


@router.post("/documents/{doc_id}/reprocess", response_model=DocumentResponse)
def reprocess_document(
    doc_id: str,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """重新向量化文档"""
    from app.models.document import Document
    from app.rag.loaders import load_document
    from app.rag.splitter import split_documents
    from app.rag.vector_store import add_documents, delete_by_document_id

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在")

    # 清除旧向量
    try:
        delete_by_document_id(doc_id)
    except Exception:
        pass

    # 重新处理
    doc.status = "processing"
    db.commit()

    try:
        raw_docs = load_document(doc.file_path)
        for d in raw_docs:
            d.metadata["doc_id"] = doc.id
            d.metadata["filename"] = doc.filename
        chunks = split_documents(raw_docs)
        add_documents(chunks)
        doc.chunk_count = len(chunks)
        doc.status = "completed"
    except Exception as e:
        doc.status = "failed"
        db.commit()
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"处理失败: {str(e)}")

    db.commit()
    return doc.to_dict()


@router.get("/stats", response_model=KnowledgeStatsResponse)
def get_stats(
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取知识库统计信息"""
    return document_service.get_stats(db)
