#!/bin/bash

# AlexClaw AI Agent 启动脚本
# 用于启动交互式AI Agent界面

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python是否可用
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ 错误: 未找到Python，请先安装Python"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# 检查虚拟环境是否存在
if [ -d "venv" ]; then
    echo "📦 检测到虚拟环境，正在激活..."
    source venv/bin/activate
fi

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  未检测到.env文件，正在从.env.example复制..."
        cp .env.example .env
        echo "📝 请编辑.env文件并配置你的API密钥"
    else
        echo "❌ 错误: 未找到.env文件或.env.example文件"
        exit 1
    fi
fi

# 启动Agent
echo "🚀 启动AlexClaw AI Agent..."
echo "   按 Ctrl+C 或输入 /quit 退出"
echo ""

$PYTHON_CMD main.py "$@"
