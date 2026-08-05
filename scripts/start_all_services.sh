#!/bin/bash
# 环境隔离检查
if [ ! -f "$(dirname "$(dirname "$0")")/.env_type" ] || [ "$(cat "$(dirname "$(dirname "$0")")/.env_type")" != "test" ]; then
    echo "❌ 安全拦截：当前不是测试环境，禁止启动"
    exit 1
fi
# 启动测试环境服务（当前三角色基线：仅保留回调入口 :5101）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT/logs"
mkdir -p "$LOG_DIR"
cd "$PROJECT"

# 仅清理本环境回调端口（5101），不碰共享服务
kill_port() {
    local port=$1
    local pid
    pid=$(lsof -ti:"$port" 2>/dev/null)
    if [ -n "$pid" ]; then
        kill "$pid" 2>/dev/null
        sleep 1
    fi
}
kill_port 5101
sleep 1

# 启动 Flask 回调服务（:5101）
nohup "$PROJECT/assistants/chat-assistant/venv-chat/bin/python" \
    "$PROJECT/shared/feishu-callback/callback_server.py" > "$LOG_DIR/flask.log" 2>&1 &
sleep 2

echo ""
echo "✅ 测试环境服务已启动"
echo ""
echo "回调 URL 配置（通过 employee-radish-fringe.ngrok-free.dev 外网访问）："
echo "  1号闲聊 / 2号办公 / 3号日程: https://employee-radish-fringe.ngrok-free.dev/webhook_chat"
echo ""
echo "⚠️  注意：当前三角色基线已移除 4 号文件助手与独立 :5102 服务；确保共享推理后端与隧道仍可访问。"
