# 压力测试使用说明

针对「100 人同时使用」的压测工具，基于 Locust。覆盖认证、问答主路径、缓存命中、写路径、冒烟五个场景。

## 一、环境准备

1. 安装依赖（复用 backend venv）：

   ```bat
   cd backend
   venv\Scripts\pip install -r stress\requirements.txt
   ```

2. 确认 `.env` 里 `DASHSCOPE_API_KEY` 有效（真实调用百炼会**产生费用**，且受账户并发配额限制）。

3. 启动后端（保持运行）：

   ```bat
   cd backend
   venv\Scripts\activate && python main.py
   ```

4. 预置测试用户（覆盖 100 并发 + 余量）：

   ```bat
   cd backend
   venv\Scripts\python stress\seed.py --users 120
   ```

## 二、压测流程（带闸门，必须先小后大）

| 步骤 | 命令 | 目的 |
|---|---|---|
| 闸门1 冒烟 | `stress\run.bat s0 1 1 30s` | 全接口通、SSE 收流正常 |
| 闸门2 配额 | `stress\run.bat s2 10 2 3m` | 看百炼是否 429、TTFT 是否正常 |
| 阶梯加压 | `stress\run.bat s2 30 5 5m` → `50` → `80` → `100` | 找吞吐拐点 |
| 稳定期 | `stress\run.bat s2 100 5 10m` | 采集 100 并发稳定指标 |
| 认证基线 | `stress\run.bat s1 50 5 3m` | bcrypt/JWT 开销 |
| 缓存命中 | `stress\run.bat s3 30 5 2m` | 命中后延迟应骤降 |
| 写路径 | `stress\run.bat s4 5 1 2m` | 上传并发写锁（小规模即可） |

> 结果 CSV 写入 `stress/results/`（已被 .gitignore 忽略）。

## 三、服务端监控（另开终端，压测时同步跑）

```bat
cd backend
:: 先查后端 python 进程 PID（任务管理器 / tasklist）
tasklist | findstr python
venv\Scripts\python stress\server_monitor.py --pid <PID> --out stress/results/server.csv
```

## 四、结果解读

- **SSE 指标**：Locust 统计里的 `SSE /chat-ttft`（首 token 延迟）和 `SSE /chat-total`（完整回答耗时）是核心。自动生成的 `POST /chat` 条目时间只是 HTTP 头部返回时间，**忽略**。
- **错误分类（重点）**：
  - `database is locked` → SQLite 写锁竞争（系统自身瓶颈）。
  - 状态码 `429` → **百炼限流**，是外部依赖的墙，不是系统 bug，单独统计、不判系统失败。
  - 其他 `5xx` → 代码 bug，需排查。
- **事件循环是否阻塞**：看 `server_monitor.csv`。若 CPU 长时间打满单核且 `chat-ttft` 同步飙升，说明同步检索阻塞了事件循环。
- **通过标准（参考）**：系统错误率 < 1%；`chat-ttft` p95 < 5s；`chat-total` p95 < 20s；login p95 < 2s；读接口 p95 < 500ms。

## 五、已知预期瓶颈（对照用）

1. `retrieval_service.hybrid_search` 是同步阻塞调用，在 async generator 里直接执行（ChromaDB 查询 + jieba + BM25），会卡事件循环。
2. `add_message` 每次问答写两次 SQLite，并发下可能 `database is locked`。
3. 未启用 slowapi 限流，突发无保护。
4. ChromaDB 单例写入与查询并发会锁。
5. 百炼并发配额 → 429。
6. 语义缓存 key 为精确小写匹配，随机问题全 miss，maxsize=200。
