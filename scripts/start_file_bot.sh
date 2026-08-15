#!/bin/bash
# 启动 4号 文件助手独立服务
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BOT_DIR="$PROJECT_DIR/assistants/file-assistant"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"

export FILE_BOT_PORT=5082
echo "🚀 启动4号文件助手服务 (端口5082)..."
cd "$PROJECT_DIR" && "$BOT_DIR/venv-file/bin/python" "$BOT_DIR/src/file_bot_server.py" >> "$LOG_DIR/file_bot.log" 2>&1 &
BOT_PID=$!
echo "✅ 文件助手服务已启动 (PID: $BOT_PID)"
echo "   日志: $LOG_DIR/file_bot.log"
echo "   端口: 5082"
echo ""
echo "停止命令: kill $BOT_PID"
