# RAG 企业级知识库问答系统

基于 **LangChain** + **阿里云百炼** + **FastAPI** + **Vue 3** 的电商知识库智能问答平台。

## 系统简介

面向电商平台的 RAG（检索增强生成）企业级知识库问答系统。上传商品相关文档构建知识库，用户可以通过自然语言提问，系统自动从知识库中检索相关信息并结合大模型生成带引用来源的答案。

## 技术栈

| 层级 | 技术 |
|------|------|
| RAG 框架 | LangChain + LangGraph |
| 后端框架 | Python FastAPI |
| 前端框架 | Vue 3 + TypeScript + Element Plus |
| 向量数据库 | ChromaDB |
| 关系数据库 | SQLite |
| LLM | 阿里云百炼 - 通义千问 qwen-plus |
| Embedding | 阿里云百炼 - text-embedding-v2 |
| 缓存 | 内存缓存 (cachetools) |
| 文档解析 | PyPDF, python-docx, openpyxl |

## 功能列表

### 基础功能
- ✅ 用户注册/登录/修改密码
- ✅ JWT Token 认证 + 角色权限控制
- ✅ 知识库文档上传（PDF/Word/Excel/TXT/MD/CSV）
- ✅ 文档自动分块 + 向量化入库
- ✅ RAG 知识库问答（流式输出）
- ✅ 回答引用知识库片段来源
- ✅ 多用户独立会话管理
- ✅ 对话历史持久化，跨登录恢复
- ✅ 管理员专属知识库管理

### 进阶优化
- 🔍 混合检索：向量检索 + BM25 关键词融合 (RRF)
- 💾 语义缓存：相似问题直接返回缓存结果
- ⚡ 流式输出：SSE 逐 token 推送，首字延迟 < 1s
- 🛡️ API 限流：内存令牌桶算法

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- 阿里云百炼 API Key（[免费注册获取](https://bailian.console.aliyun.com)）

### 2. 配置 API Key

编辑 `backend/.env` 文件，填入你的百炼 API Key：
```env
DASHSCOPE_API_KEY=sk-你的API-Key
```

> ⚠️ API Key 已经配置好了，如果过期请自行更新。

### 3. Windows 本地启动

#### 方式一：一键启动（推荐）

```batch
# 在项目根目录双击运行，或在 cmd 中执行：
start.bat
```

#### 方式二：手动启动

**步骤 1：建立 Python 虚拟环境并安装依赖**

打开 cmd.exe，进入项目目录：
```batch
cd /d D:\LangChainRAG项目\backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**步骤 2：启动后端服务**
```batch
# 确认在 backend 目录且 venv 已激活
python main.py
```
后端运行在：http://localhost:8000
API 文档：http://localhost:8000/docs

**步骤 3：启动前端服务**

打开新的 cmd.exe 终端：
```batch
cd /d D:\LangChainRAG项目\frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```
前端运行在：http://localhost:5173

### 4. 访问系统

1. 浏览器打开 http://localhost:5173
2. 使用管理员账号登录：`admin` / `123456`
3. 进入「知识库管理」上传商品文档
4. 注册普通用户账号，开始知识库问答

## 项目结构

```
langchain-rag-qa/
├── backend/                    # 后端
│   ├── app/
│   │   ├── api/                # API 路由
│   │   │   ├── auth.py         # 用户认证
│   │   │   ├── chat.py         # SSE 问答
│   │   │   ├── conversation.py # 会话管理
│   │   │   └── knowledge.py    # 知识库管理
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       # 全局配置
│   │   │   ├── database.py     # SQLAlchemy
│   │   │   └── security.py     # JWT + 权限
│   │   ├── models/             # 数据库模型
│   │   ├── schemas/            # Pydantic 校验
│   │   ├── services/           # 业务逻辑
│   │   │   ├── rag_service.py       # RAG 问答
│   │   │   ├── document_service.py  # 文档处理
│   │   │   ├── retrieval_service.py # 混合检索
│   │   │   ├── conversation_service.py
│   │   │   └── user_service.py
│   │   └── rag/                # LangChain RAG 组件
│   │       ├── loaders.py      # 文档加载器
│   │       ├── splitter.py     # 文本分割
│   │       ├── embeddings.py   # Embedding 模型
│   │       ├── vector_store.py # ChromaDB
│   │       └── chain.py        # RAG Chain
│   ├── .env                    # 环境变量（API Key）
│   ├── main.py                 # FastAPI 入口
│   └── requirements.txt
├── frontend/                   # 前端
│   ├── src/
│   │   ├── views/              # 页面
│   │   │   ├── Login.vue
│   │   │   ├── Register.vue
│   │   │   ├── ChatView.vue    # 问答主界面
│   │   │   ├── AdminView.vue   # 知识库管理
│   │   │   └── Profile.vue     # 个人中心
│   │   ├── api/                # API 请求
│   │   ├── stores/             # Pinia 状态
│   │   └── router/             # 路由守卫
│   └── package.json
└── start.bat                   # 一键启动脚本
```

## API 文档

启动后端后访问：**http://localhost:8000/docs**（FastAPI 自动生成 Swagger）

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 |
| POST | /api/auth/change-password | 改密 |
| GET | /api/auth/me | 当前用户 |
| GET | /api/conversations | 会话列表 |
| POST | /api/conversations | 创建会话 |
| PATCH | /api/conversations/{id} | 重命名 |
| DELETE | /api/conversations/{id} | 删除会话 |
| GET | /api/conversations/{id}/messages | 历史消息 |
| POST | /api/conversations/{id}/chat | **问答（SSE流式）** |
| GET | /api/knowledge/documents | 文档列表 |
| POST | /api/knowledge/upload | 上传文档 |
| DELETE | /api/knowledge/documents/{id} | 删除文档 |

## 开发说明

### RAG 问答流程

```
用户提问 → 语义缓存检查
         → 混合检索（向量 + BM25 → RRF 融合）
         → 上下文组装（拼接 Top-5 片段）
         → LLM 流式生成（阿里云百炼 qwen-plus）
         → 返回答案 + 引用来源标注 [N]
```

### 预设账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 123456 |
| 普通用户 | 自行注册 | 自行设置 |

- **管理员**：可上传/管理知识库文档 + 进行问答
- **普通用户**：仅可进行知识库问答
