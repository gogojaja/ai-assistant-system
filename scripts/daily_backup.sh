#!/bin/bash
# 每日备份脚本（crontab: 每天 24:00）
# 备份到外部卷 /Volumes/WDC500G/old_projects/
BACKUP_DIR="/Volumes/WDC500G/old_projects"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)
ARCHIVE="$BACKUP_DIR/ai-assistant-system_$DATE.tar.gz"
PROJECT="$HOME/ai-assistant-system"

# 打包（排除大型可重建目录）
tar -czf "$ARCHIVE" \
  -C "$HOME" \
  --exclude="ai-assistant-system/venv" \
  --exclude="ai-assistant-system/assistants/*/venv-*" \
  --exclude="ai-assistant-system/backups" \
  --exclude="ai-assistant-system/logs/*.log" \
  --exclude="ai-assistant-system/.crypto_key" \
  --exclude="ai-assistant-system/**/__pycache__" \
  ai-assistant-system 2>/dev/null

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$ARCHIVE" | cut -f1)
    echo "[$(date)] 备份成功: $ARCHIVE ($SIZE)"
else
    echo "[$(date)] 备份失败"
fi

# 保留最近 30 天
find "$BACKUP_DIR" -name "ai-assistant-system_*.tar.gz" -mtime +30 -delete 2>/dev/null
