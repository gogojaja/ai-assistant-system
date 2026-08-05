#!/bin/bash
# 测试环境服务守护 — 当前三角色基线，仅监控本环境回调服务（:5101）
# 不管理共享服务（llama-server、ngrok），不碰主环境进程
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT/logs"
LOG_FILE="$LOG_DIR/monitor.log"
mkdir -p "$LOG_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

check_service() {
    local port=$1
    local name=$2
    local cmd=$3
    if ! lsof -i tcp:"$port" > /dev/null 2>&1; then
        log "⚠️  $name 未监听 :$port，正在重启..."
        eval "$cmd"
        sleep 3
        if lsof -i tcp:"$port" > /dev/null 2>&1; then
            log "✅ $name 已恢复"
        else
            log "❌ $name 启动失败"
        fi
    fi
}

log "====== 测试环境服务守护启动 ======"

while true; do
    check_service 5101 "Flask 回调" \
        "nohup '$PROJECT/assistants/chat-assistant/venv-chat/bin/python' \
               '$PROJECT/shared/feishu-callback/callback_server.py' > '$LOG_DIR/flask.log' 2>&1 &"

    sleep 60
done
