#!/bin/bash
# 启动测试环境服务（共享推理后端和 ngrok，仅启动本环境回调 + file_bot + sys_bot）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT/logs"
mkdir -p "$LOG_DIR"
cd "$PROJECT"

# 仅清理本环境端口（5101/5102/5103），不碰共享服务
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
kill_port 5102
kill_port 5103
sleep 1

# 启动 Flask 回调服务（:5101）
export FILE_BOT_PORT=5102
export SYS_BOT_PORT=5103

nohup "$PROJECT/assistants/chat-assistant/venv-chat/bin/python" \
    "$PROJECT/shared/feishu-callback/callback_server.py" > "$LOG_DIR/flask.log" 2>&1 &
sleep 2

# 启动 4号 文件助手服务（:5102）
nohup "$PROJECT/assistants/file-assistant/venv-file/bin/python" \
    "$PROJECT/assistants/file-assistant/src/file_bot_server.py" >> "$LOG_DIR/file_bot.log" 2>&1 &
echo "4号文件助手已启动 (PID: $!)"

# 启动 5号 系统管理服务（:5103）
nohup "$PROJECT/assistants/sys-assistant/venv-sys/bin/python" \
    "$PROJECT/assistants/sys-assistant/src/bot_server.py" >> "$LOG_DIR/sys_bot.log" 2>&1 &
echo "5号系统管理已启动 (PID: $!)"

sleep 2

echo ""
echo "✅ 测试环境服务已启动"
echo ""
echo "回调 URL 配置（通过 employee-radish-fringe.ngrok-free.dev 外网访问）："
echo "  1号闲聊: https://employee-radish-fringe.ngrok-free.dev/webhook_chat"
echo "  2号办公: https://employee-radish-fringe.ngrok-free.dev/webhook_chat"
echo "  3号日程: https://employee-radish-fringe.ngrok-free.dev/webhook_chat"
echo "  4号文件: https://employee-radish-fringe.ngrok-free.dev/webhook_file"
echo "  5号系统: https://employee-radish-fringe.ngrok-free.dev/webhook_sys"
echo ""
echo "⚠️  注意：确保主环境已启动共享服务（llama-server + ngrok 隧道）"
