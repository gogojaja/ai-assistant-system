#!/bin/bash
# 模型备份脚本：查询并备份所有项目中使用的模型文件
# 目标：/Volumes/WDC500G/model_backups/
set -e

TARGET="/Volumes/WDC500G/model_backups"
mkdir -p "$TARGET"
LOG="$TARGET/backup_models.log"

echo "=== 模型备份 $(date) ===" | tee -a "$LOG"
echo "目标: $TARGET" | tee -a "$LOG"
echo "" | tee -a "$LOG"

# 1. 推理模型：Ollama blobs（正在使用的 Qwen3:4b + 其他已下载的 blob）
echo "--- 1. 推理模型 (Ollama blobs) ---" | tee -a "$LOG"
BLOBS_DIR="$HOME/.local/lib/ollama/blobs"
if [ -d "$BLOBS_DIR" ]; then
    for f in "$BLOBS_DIR"/sha256-*; do
        name=$(basename "$f")
        size=$(du -h "$f" | cut -f1)
        echo "  $name ($size)" | tee -a "$LOG"
        cp -n "$f" "$TARGET/$name" 2>/dev/null && echo "    ✅ 已备份" | tee -a "$LOG"
    done
else
    echo "  未找到 ollama blobs 目录" | tee -a "$LOG"
fi
echo "" | tee -a "$LOG"

# 2. Whisper 语音模型
echo "--- 2. Whisper 语音模型 ---" | tee -a "$LOG"
WHISPER_DIR="$HOME/ai-assistant-system/shared/whisper.cpp/models"
if [ -d "$WHISPER_DIR" ]; then
    for f in "$WHISPER_DIR"/ggml-*.bin; do
        name=$(basename "$f")
        size=$(du -h "$f" | cut -f1)
        echo "  $name ($size)" | tee -a "$LOG"
        cp -n "$f" "$TARGET/$name" 2>/dev/null && echo "    ✅ 已备份" | tee -a "$LOG"
    done
else
    echo "  未找到 whisper 模型目录" | tee -a "$LOG"
fi
echo "" | tee -a "$LOG"

# 汇总
echo "=== 备份完成 ===" | tee -a "$LOG"
echo "目标目录大小:" | tee -a "$LOG"
du -sh "$TARGET" | tee -a "$LOG"
echo "========================" | tee -a "$LOG"
