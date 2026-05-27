#!/bin/bash
# 启动测试环境 4/5号 Bot（file_bot :5102 + sys_bot :5103，不启动 ngrok）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT/logs"
mkdir -p "$LOG_DIR"
cd "$PROJECT"

echo "🚀 启动测试环境 4/5号 Bot 服务..."

# 停止旧实例
kill_port() {
    local pid
    pid=$(lsof -ti:"$1" 2>/dev/null)
    [ -n "$pid" ] && kill "$pid" 2>/dev/null; sleep 1
}
kill_port 5102
kill_port 5103
sleep 1

# 启动 4号 文件助手（:5102）
export FILE_BOT_PORT=5102
nohup "$PROJECT/assistants/file-assistant/venv-file/bin/python" \
    "$PROJECT/assistants/file-assistant/src/file_bot_server.py" >> "$LOG_DIR/file_bot.log" 2>&1 &
echo "  4号文件助手已启动 (PID: $!)"

# 启动 5号 系统管理（:5103）
export SYS_BOT_PORT=5103
nohup "$PROJECT/assistants/sys-assistant/venv-sys/bin/python" \
    "$PROJECT/assistants/sys-assistant/src/bot_server.py" >> "$LOG_DIR/sys_bot.log" 2>&1 &
echo "  5号系统管理已启动 (PID: $!)"

sleep 2

echo ""
echo "✅ 测试环境 4/5号 Bot 已启动"
echo "  4号文件: https://employee-radish-fringe.ngrok-free.dev/webhook_file"
echo "  5号系统: https://employee-radish-fringe.ngrok-free.dev/webhook_sys"
echo ""
echo "  1/2/3号 Bot 不受影响"
