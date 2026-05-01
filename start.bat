@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM AlexClaw AI Agent 启动脚本
REM 用于启动交互式AI Agent界面

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 检查Python是否可用
where python >nul 2>&1
if %errorlevel% neq 0 (
    where python3 >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ 错误: 未找到Python，请先安装Python
        exit /b 1
    )
    set "PYTHON_CMD=python3"
) else (
    set "PYTHON_CMD=python"
)

REM 检查虚拟环境是否存在
if exist "venv\Scripts\activate.bat" (
    echo 📦 检测到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
)

REM 检查.env文件是否存在
if not exist ".env" (
    if exist ".env.example" (
        echo ⚠️  未检测到.env文件，正在从.env.example复制...
        copy ".env.example" ".env"
        echo 📝 请编辑.env文件并配置你的API密钥
    ) else (
        echo ❌ 错误: 未找到.env文件或.env.example文件
        exit /b 1
    )
)

REM 启动Agent
echo 🚀 启动AlexClaw AI Agent...
echo    按 Ctrl+C 或输入 /quit 退出
echo.

%PYTHON_CMD% main.py %*
