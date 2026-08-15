---
name: security-audit
description: 安全审计 — 检测敏感信息泄露、注入漏洞、配置风险等安全隐患
model: sonnet
---

# 安全审计技能

## 技能说明

本技能用于对「RAG 企业级知识库问答系统」项目进行全面的代码安全检查，发现潜在的安全隐患并给出修复方案。

---

## 执行流程

### 第一步：确定审计范围

询问用户想审计哪些内容：
- **全部代码**：`backend/`、`frontend/`、根目录配置文件的完整审计
- **指定目录**：例如只审计 `backend/app/api/` 或 `backend/app/services/`
- **当前改动**：`git diff --name-only main` 看相比主分支改了什么，只审计改动部分
- **配置文件专项**：只检查 `.env`、`.gitignore`、`requirements.txt`、`frontend/package.json` 等

### 第二步：逐项检查（四大维度）

---

## 维度一：敏感信息泄露 🔑

### 检查目标

在代码、注释、配置文件中搜索可能泄露的敏感信息。

### 搜索模式

```
硬编码 API Key / 密钥：
  DASHSCOPE_API_KEY = "sk-..."
  api_key = "..."、apiKey = "..."
  SECRET_KEY = "..."、jwt_secret = "..."

数据库凭证：
  DATABASE_URL = "..."（含密码的连接串）
  db_password = "..."

私钥/证书：
  -----BEGIN RSA PRIVATE KEY-----
  -----BEGIN CERTIFICATE-----

内网地址：
  192.168.x.x、10.x.x.x、172.16-31.x.x

个人信息：
  手机号 1[3-9]\d{9}
  身份证号 \d{17}[\dXx]
```

### 判定标准

| 严重程度 | 场景 | 示例 |
|----------|------|------|
| 🔴 严重 | 代码中直接写了 API Key / 密钥 | `DASHSCOPE_API_KEY = "sk-abc123"` |
| 🟡 警告 | 注释中残留了测试密钥 | `# 测试用 key: sk-test123` |
| 🟢 安全 | 从环境变量读取配置 | `os.getenv("DASHSCOPE_API_KEY")` |

### 报告格式

```
🔑 敏感信息泄露 — 发现 X 处问题

🔴 严重（共 A 处）
📍 位置：backend/app/core/config.py:12
❌ 阿里云百炼 API Key 硬编码在代码中
✅ 建议：改用环境变量 os.getenv("DASHSCOPE_API_KEY")，配置写到 .env 且不提交
```

---

## 维度二：注入漏洞风险 💉

### 检查目标

检查代码中是否存在 SQL 注入、命令注入、XSS、路径遍历等风险。

### 检查点

**SQL 注入**（项目用 SQLAlchemy ORM）：
- 是否用了字符串拼接构造 SQL？
  ```python
  ❌ session.execute(text(f"SELECT * FROM users WHERE id = '{user_id}'"))
  ✅ 使用 ORM 查询：session.get(User, user_id) 或参数化 text()
  ```
- 用户输入（用户名、会话 id、文档名）有没有直接拼进 SQL？

**命令注入**：
- 有没有用 `subprocess`、`os.system`、`os.popen` 执行用户可控的命令？（文档解析、文件处理时尤其注意）

**XSS（跨站脚本）**：
- 前端是否用 `v-html` 或 `innerHTML` 直接渲染用户/LLM 输出的内容？
  ```html
  ❌ <div v-html="answerHtml">
  ✅ 用 markdown-it 渲染时开启 html: false，或对输出做转义
  ```
- markdown-it 渲染 LLM 回答时，是否关闭了原始 HTML？（防止回答里注入脚本）

**路径遍历**：
- 文件上传（知识库文档）时，路径是否包含用户输入？
  ```python
  ❌ open(f"uploads/{file.filename}", "wb")
  ✅ 用 uuid 重命名文件 + 校验扩展名白名单，不信任原始文件名
  ```
- 文档删除/读取接口是否校验了文档 id 的归属（越权访问）？

**提示词注入（RAG 特有）**：
- 上传的知识库文档内容是否会被直接拼进 LLM 的 system prompt？恶意文档可能诱导 LLM 泄露系统提示词或越权。

### 报告格式

```
💉 注入漏洞风险 — 发现 X 处问题

🔴 SQL 注入（共 A 处）
📍 位置：backend/app/services/user_service.py:45
❌ SQL 用 f-string 拼接用户输入
✅ 建议：改用 SQLAlchemy ORM 查询或参数化 text()，从根本上杜绝注入
```

---

## 维度三：配置文件敏感信息 📁

### 检查目标

检查所有配置文件中是否包含明文敏感信息。

### 检查范围

| 文件 | 检查内容 |
|------|----------|
| `backend/.env` | 是否包含明文 API Key（.env 不应提交到 Git） |
| `.gitignore` | 是否忽略了 .env、uploads/、chroma_data/、*.db |
| `requirements.txt` | 依赖是否过旧、是否有已知漏洞 |
| `frontend/package.json` | 是否暴露内部脚本、API 地址 |
| `README.md` | 是否暴露了真实 API Key、账号密码 |
| 各种 `.json` 配置文件 | 是否包含凭证信息 |

### 额外检查

- `.gitignore` 里有没有忽略 `.env`、`*.pem`、`*.key`、`uploads/`？
  ```
  ❌ .gitignore 里缺少 .env → API Key 可能被误提交到 Git
  ✅ .gitignore 包含 .env、uploads/、chroma_data/
  ```

- 前端代码里有没有硬编码后端 API Key？（DASHSCOPE_API_KEY 只能存在于后端）

### 报告格式

```
📁 配置文件风险 — 发现 X 处问题

🟡 警告（共 B 处）
📍 文件：.gitignore
❌ 没有忽略 uploads/ 目录，上传文档可能被误提交
✅ 建议：添加 uploads/ 到 .gitignore
```

---

## 维度四：其他安全隐患 🛡️

### 检查点

**依赖安全**：
- `requirements.txt` 中的依赖包是否有已知漏洞？（可运行 `pip-audit`）
- `frontend/package.json` 依赖是否有已知漏洞？（可运行 `npm audit`）
- 有没有依赖是直接从 git/personal repo 拉的？

**认证与授权**：
- JWT 密钥（SECRET_KEY）是否从环境变量读取、且强度足够？
- 是否所有需要登录的接口都校验了 JWT / 权限？（普通用户能否访问管理员接口）
- 密码哈希是否用了 bcrypt（passlib）而非明文或弱哈希？
- 管理员专属的知识库管理接口是否有角色校验？

**CORS 配置**：
- FastAPI 的 CORS 是否配置了 `allow_origins=["*"]` 且 `allow_credentials=True`？（危险组合）

**数据安全**：
- 用户密码、会话数据是否加密存储？
- 上传的知识库文档是否做了大小限制、类型白名单？
- SQLite / ChromaDB 数据文件是否在 .gitignore 中？

**日志安全**：
- `print` / `logger` 是否打印了敏感信息（密码、完整 API Key、JWT token）？
- 错误日志是否暴露了内部文件路径或数据库结构？

**HTTP vs HTTPS**：
- 调用阿里云百炼 API 是否强制使用 HTTPS？
- 前端 axios 的 baseURL 是否配置正确？

**调试代码**：
- 生产代码中是否残留了调试工具？（如 `print` 调试、`breakpoint()`）
- 是否有注释掉的"临时绕过"代码？（如 `# 跳过权限校验`）

### 报告格式

```
🛡️ 其他安全隐患 — 发现 X 处问题

🔴 严重（共 C 处）
📍 位置：backend/app/api/knowledge.py:30
❌ 管理员接口未做角色校验，普通用户可直接上传/删除文档
✅ 建议：在依赖注入中校验用户角色，非管理员返回 403
```

---

### 第三步：风险评级

对每个发现的问题标注严重程度：

| 级别 | 图标 | 含义 | 示例 |
|------|------|------|------|
| 严重 | 🔴 | 可被直接利用，必须立即修复 | 硬编码 API Key、SQL 注入、越权访问 |
| 警告 | 🟡 | 存在隐患，建议尽快修复 | 缺少 .env gitignore、日志泄露路径 |
| 建议 | 🟢 | 最佳实践建议，可择机改进 | 更新依赖版本、开启 markdown 转义 |

### 第四步：生成总报告

```
📊 安全审计总报告
═══════════════════════════════════
📁 审计文件数：X 个
🔴 严重问题：A 个
🟡 警告问题：B 个
🟢 改进建议：C 个

───────────────────────────────────
🔑 敏感信息泄露：  X 处（严重 A / 警告 B）
💉 注入漏洞风险：  X 处（严重 A / 警告 B）
📁 配置文件风险：  X 处（警告 B / 建议 C）
🛡️ 其他安全隐患：X 处（严重 A / 警告 B / 建议 C）
───────────────────────────────────

🏆 安全评分：[A+/A/B/C/D/F]

📌 优先修复清单（按危险程度排序）：
  1. 🔴 [最紧急的问题]
  2. 🔴 [其次紧急]
  3. 🟡 [...]
```

### 第五步：修复建议

对每个问题，给出：
1. **风险说明** — 用通俗语言解释"黑客能利用这个做什么"
2. **修复方案** — 具体的代码修改（可以用 Edit 直接帮用户改）
3. **预防措施** — 怎么避免以后再犯同样的问题

---

## 注意事项

### 项目特定关注点

- 本项目是 **B/S 架构**：后端 FastAPI + 前端 Vue3，数据经过服务器，需重点防范 API 攻击
- 阿里云百炼 **API Key 是核心敏感信息**，泄露会导致盗刷，必须只存在后端 .env 且不提交
- JWT 认证 + 角色权限控制是访问控制的核心，越权是高风险项
- 知识库文档上传涉及文件处理，**路径遍历 + 文件类型校验**需重点检查
- RAG 特有的**提示词注入**：恶意文档可能诱导 LLM 泄露信息，上传内容需谨慎拼入 prompt

### 误报处理

- 如果代码中的"密码"字样实际上是"密码输入框的 placeholder 文案"，不算泄露
- 测试文件（`backend/tests/`）中的测试数据不判定为泄露
- `.venv/`、`node_modules/`、`dist/`、`chroma_data/` 等目录不审计

### 沟通规范

- 用通俗语言解释安全风险，不堆砌专业术语
- 对每个严重问题，必须解释"黑客能怎么利用"
- 修复建议直接给出可操作的代码
- 报告全部用中文
