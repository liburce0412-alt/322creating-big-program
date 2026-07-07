@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title CampusAI 校园达人

echo ================================================
echo   CampusAI 校园达人 - 时间管理系统
echo ================================================
echo.

cd /d "%~dp0backend"

echo [启动] 正在初始化数据库...
echo [启动] 正在启动 Flask 后端服务...

REM 优先使用 PATH 中的 python，否则尝试常见路径
set PYTHON=python
where python >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON=D:\AppStore\python\python.exe
)

"%PYTHON%" -X utf8 app.py

pause
