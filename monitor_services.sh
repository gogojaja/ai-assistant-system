#!/bin/bash
cd ~/ai-assistant-system
source /Users/gogo/ai-assistant-system/venv/bin/activate
while true; do
  if ! curl -s --connect-timeout 5 http://localhost:5001/health > /dev/null 2>&1; then
    echo "$(date) - Flask 5001 无响应，重启回调服务..."
    pkill -f "shared/feishu-callback/callback_server.py"
    nohup python /Users/gogo/ai-assistant-system/shared/feishu-callback/callback_server.py > logs/flask.log 2>&1 &
    sleep 2
    if curl -s --connect-timeout 5 http://localhost:5001/health > /dev/null 2>&1; then
      echo "$(date) - Flask 已恢复"
    else
      echo "$(date) - Flask 恢复失败，请检查日志"
    fi
  fi
  sleep 30
done
