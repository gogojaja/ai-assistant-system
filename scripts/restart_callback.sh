#!/bin/bash
# 单独重启测试环境飞书回调服务（:5101）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT"
LOG_DIR="$PROJECT/logs"
mkdir -p "$LOG_DIR"

echo "正在停止旧回调服务..."
pid=$(lsof -ti:5101 2>/dev/null)
[ -n "$pid" ] && kill "$pid" 2>/dev/null
sleep 2

echo "启动回调服务（:5101）..."
nohup "$PROJECT/assistants/chat-assistant/venv-chat/bin/python" \
    "$PROJECT/shared/feishu-callback/callback_server.py" > "$LOG_DIR/flask.log" 2>&1 &
sleep 3

if lsof -ti:5101 > /dev/null 2>&1; then
    echo "✅ 回调服务已启动（:5101）"
    tail -5 "$PROJECT/logs/flask.log"
else
    echo "❌ 启动失败，请查看 logs/flask.log"
    tail -20 "$PROJECT/logs/flask.log"
fi
