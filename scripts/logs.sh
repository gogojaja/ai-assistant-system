#!/bin/bash
# 查看各服务的最新日志
LOG_DIR="$HOME/ai-assistant-system/logs"

echo "===== Ollama 日志 (最后20行) ====="
tail -20 "$LOG_DIR/ollama.log" 2>/dev/null || echo "无日志文件"

echo -e "\n===== Flask 回调服务日志 (最后20行) ====="
tail -20 "$LOG_DIR/flask.log" 2>/dev/null || echo "无日志文件"

echo -e "\n===== Cloudflared 隧道日志 (最后20行) ====="
tail -20 "$LOG_DIR/cloudflared.log" 2>/dev/null || echo "无日志文件"

echo -e "\n===== 实时跟踪日志 (按 Ctrl+C 退出) ====="
echo "使用以下命令分别跟踪:"
echo "  tail -f $LOG_DIR/flask.log"
echo "  tail -f $LOG_DIR/cloudflared.log"
