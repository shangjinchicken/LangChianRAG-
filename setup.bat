@echo off
chcp 65001 >nul
echo ============================================
echo   RAG 知识库问答系统 - 环境安装
echo ============================================
echo.

:: 检查 Python
echo [检查] Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

:: 检查 Node.js
echo [检查] Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
node --version

echo.
echo ============================================
echo   第一步：安装后端 Python 依赖
echo ============================================
cd /d "%~dp0backend"

:: 创建虚拟环境（如果不存在）
if not exist "venv\Scripts\python.exe" (
    echo [创建] Python 虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 升级 pip
echo [升级] pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

:: 安装依赖
echo.
echo [安装] 后端依赖（预计 2-5 分钟）...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    echo.
    echo [警告] 清华镜像安装失败，尝试默认源...
    pip install -r requirements.txt
)

echo.
echo ============================================
echo   第二步：安装前端 npm 依赖
echo ============================================
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [安装] 前端依赖（预计 1-2 分钟）...
    call npm install
)

echo.
echo ============================================
echo   安装完成！
echo ============================================
echo.
echo 启动方式：
echo   终端1: cd backend ^&^& venv\Scripts\activate ^&^& python main.py
echo   终端2: cd frontend ^&^& npm run dev
echo.
echo 或者双击 start.bat 一键启动
echo.
pause
