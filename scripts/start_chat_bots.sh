#!/bin/bash
# 启动测试环境 1/2/3号 Bot（callback_server :5101，当前三角色基线）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT/logs"
mkdir -p "$LOG_DIR"
cd "$PROJECT"

echo "🚀 启动测试环境 1/2/3号 Bot 服务..."

# 停止旧实例
kill_port() {
    local pid
    pid=$(lsof -ti:"$1" 2>/dev/null)
    [ -n "$pid" ] && kill "$pid" 2>/dev/null
}
kill_port 5101
sleep 2

# 启动 Flask 回调服务（:5101）
nohup "$PROJECT/assistants/chat-assistant/venv-chat/bin/python" \
    "$PROJECT/shared/feishu-callback/callback_server.py" > "$LOG_DIR/flask.log" 2>&1 &
sleep 2

echo ""
echo "✅ 测试环境 1/2/3号 Bot 已启动"
echo "  回调 URL: https://employee-radish-fringe.ngrok-free.dev/webhook_chat"
echo ""
echo "  当前三角色基线仅保留 1/2/3 号助手，不再维护旧 4 号文件助手。"
