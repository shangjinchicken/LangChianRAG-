@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   RAG Knowledge QA System - Start
echo ============================================
echo.

:: Start backend
echo [1/2] Starting backend server...
start "RAG-Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate.bat && python main.py"

:: Wait for backend
echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting frontend server...
start "RAG-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo   Backend:  http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo   Frontend: http://localhost:5176
echo ============================================
echo.
echo Press any key to close this window...
pause >nul
