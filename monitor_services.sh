#!/bin/bash
# 测试环境守护脚本：只管理当前工作区 /Volumes/BR256G/ai-assistant-system
# 目标端口：5101，避免误碰主环境 5001/5002/5003

PROJECT_ROOT="/Volumes/BR256G/ai-assistant-system"
CALLBACK_PORT=5101
CALLBACK_PYTHON="$PROJECT_ROOT/assistants/chat-assistant/venv-chat/bin/python"
CALLBACK_SCRIPT="$PROJECT_ROOT/shared/feishu-callback/callback_server.py"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

while true; do
  if ! curl -s --connect-timeout 5 "http://127.0.0.1:$CALLBACK_PORT/health" > /dev/null 2>&1; then
    log "Flask :$CALLBACK_PORT 无响应，重启回调服务..."
    pkill -f "$CALLBACK_SCRIPT" || true
    nohup "$CALLBACK_PYTHON" "$CALLBACK_SCRIPT" > "$LOG_DIR/flask.log" 2>&1 &
    sleep 2
    if curl -s --connect-timeout 5 "http://127.0.0.1:$CALLBACK_PORT/health" > /dev/null 2>&1; then
      log "Flask 已恢复"
    else
      log "Flask 恢复失败，请检查 $LOG_DIR/flask.log"
    fi
  fi
  sleep 30
done
