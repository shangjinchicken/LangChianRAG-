"""FastAPI 应用入口"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base, SessionLocal
from app.core import settings
from app.api import auth, chat, conversation, knowledge
from app.services.user_service import init_admin


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    app = FastAPI(
        title="RAG 企业级知识库问答系统",
        description="基于 LangChain + 阿里云百炼的电商知识库问答系统",
        version="1.0.0",
    )

    # CORS 跨域（允许前端开发服务器访问）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5176", "http://127.0.0.1:5176"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(auth.router)
    app.include_router(conversation.router)
    app.include_router(chat.router)
    app.include_router(knowledge.router)

    # 启动事件：初始化数据库和管理员账户
    @app.on_event("startup")
    def on_startup():
        # 创建数据库表
        Base.metadata.create_all(bind=engine)
        # 初始化管理员
        db = SessionLocal()
        try:
            init_admin(db)
        finally:
            db.close()
        print(f"[OK] App started: http://localhost:{settings.port}")
        print(f"[OK] API Docs: http://localhost:{settings.port}/docs")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
