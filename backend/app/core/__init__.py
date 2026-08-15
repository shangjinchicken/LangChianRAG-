"""应用全局配置"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，自动从 .env 文件和环境变量加载"""

    # 阿里云百炼
    dashscope_api_key: str = ""

    # JWT
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 1440  # 24小时

    # 数据库
    database_url: str = "sqlite:///./app.db"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"

    # 文件上传
    upload_dir: str = "./uploads"

    # 服务端口
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# 设置 dashscope 全局 API Key（Tongyi LLM 依赖全局变量而非构造参数）
import dashscope
dashscope.api_key = settings.dashscope_api_key

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.chroma_persist_dir, exist_ok=True)
