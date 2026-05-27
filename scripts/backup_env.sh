#!/bin/bash
# 每日环境配置备份脚本（无 sudo 权限）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT/env_backups"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/env_backup_$DATE.txt"

echo "=== 环境配置备份 $DATE ===" > "$BACKUP_FILE"
echo "Python 版本: $(python3 --version 2>&1)" >> "$BACKUP_FILE"
echo "Ollama 版本: $(ollama --version 2>&1)" >> "$BACKUP_FILE"
echo "已安装模型: $(ollama list)" >> "$BACKUP_FILE"
echo "飞书 App ID: $(grep FEISHU_APP_ID "$PROJECT/shared/feishu-bot/.env" | cut -d= -f2)" >> "$BACKUP_FILE"
echo "虚拟环境列表:" >> "$BACKUP_FILE"
ls -d "$PROJECT"/assistants/*/venv-* >> "$BACKUP_FILE"
echo "Flask 服务 PID: $(pgrep -f callback_server.py)" >> "$BACKUP_FILE"
echo "隧道进程: $(pgrep -f 'cloudflared|ssh.*pinggy')" >> "$BACKUP_FILE"
echo "备份完成: $BACKUP_FILE"
