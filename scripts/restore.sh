#!/bin/bash
# 一键还原脚本
# 用法: bash scripts/restore.sh              # 列出可用备份
#        bash scripts/restore.sh <备份文件>   # 还原

BACKUP_DIR="$HOME/backups/ai-assistant-system"
PROJECT_DIR="$HOME/ai-assistant-system"
LOG_DIR="$PROJECT_DIR/logs"
STAMP="$PROJECT_DIR/.restore_stamp"

mkdir -p "$LOG_DIR"

if [ $# -eq 0 ]; then
    echo "可用的备份文件："
    echo ""
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print NR")", $NF, "(" $5 ")", $6, $7, $8}'
    echo ""
    echo "还原命令示例："
    LATEST=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST" ]; then
        echo "  bash scripts/restore.sh $(basename "$LATEST")"
    fi
    exit 0
fi

ARCHIVE="$1"
if echo "$ARCHIVE" | grep -q /; then
    [ -f "$ARCHIVE" ] || { echo "❌ 文件不存在: $ARCHIVE"; exit 1; }
else
    [ -f "$BACKUP_DIR/$ARCHIVE" ] || { echo "❌ 文件不存在: $BACKUP_DIR/$ARCHIVE"; exit 1; }
    ARCHIVE="$BACKUP_DIR/$ARCHIVE"
fi

echo "⚠️  即将还原：$(basename "$ARCHIVE")"
echo "    目标目录：$PROJECT_DIR"
echo "    当前目录将被覆盖！"
echo ""
echo -n "是否继续？(yes/no): "
read -r CONFIRM
[ "$CONFIRM" = "yes" ] || { echo "已取消"; exit 0; }

# 停止所有服务
echo "正在停止服务..."
pkill -f callback_server.py 2>/dev/null
pkill -f llama-server 2>/dev/null
pkill -f ollama 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 2

# 备份当前目录（带时间戳）
PREV_BACKUP="$BACKUP_DIR/prev_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "正在备份当前项目..."
tar -czf "$PREV_BACKUP" -C "$HOME" ai-assistant-system 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ 当前项目已备份至：$(basename "$PREV_BACKUP")"
fi

# 还原
echo "正在还原..."
rm -rf "$PROJECT_DIR"
tar -xzf "$ARCHIVE" -C "$HOME" 2>/dev/null
if [ $? -eq 0 ]; then
    date +%s > "$STAMP"
    echo "✅ 还原成功：$(basename "$ARCHIVE")"
    echo "   还原时间戳已写入 $STAMP"
    echo ""
    echo "启动服务：bash scripts/start_all_services.sh"
else
    echo "❌ 还原失败"
    exit 1
fi
