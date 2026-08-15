"""pytest 全局配置和共享 fixtures"""
import sys
import os

# 将 backend 目录加入 Python 路径，确保 `from app.xxx` 导入正常
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
