@echo off
chcp 65001 >nul
setlocal

REM 用法: run.bat <tag> <users> <spawn-rate> <run-time>
REM 例:
REM   run.bat s0 1 1 30s       冒烟
REM   run.bat s2 10 2 3m       10 并发验证配额
REM   run.bat s2 100 5 10m     100 并发阶梯目标
REM   run.bat s1 50 5 3m       认证基线
REM   run.bat s3 30 5 2m       缓存命中
REM   run.bat s4 5 1 2m        写路径

set TAG=%1
set USERS=%2
set RATE=%3
set RUNTIME=%4

if "%TAG%"=="" set TAG=s0
if "%USERS%"=="" set USERS=1
if "%RATE%"=="" set RATE=1
if "%RUNTIME%"=="" set RUNTIME=30s

REM s0~s4 映射到对应的 User 类
set CLASS=SmokeUser
if "%TAG%"=="s1" set CLASS=AuthUser
if "%TAG%"=="s2" set CLASS=ChatUser
if "%TAG%"=="s3" set CLASS=CacheUser
if "%TAG%"=="s4" set CLASS=WriteUser

cd /d %~dp0
if not exist results mkdir results

..\venv\Scripts\python -m locust -f locustfile.py ^
  --host http://localhost:8001 ^
  --users %USERS% ^
  --spawn-rate %RATE% ^
  --run-time %RUNTIME% ^
  --headless ^
  --csv results\%TAG%_u%USERS% ^
  %CLASS%

endlocal
