#!/bin/bash
# Ollama 启动脚本
if pgrep -q ollama; then
    echo "Ollama 已在运行"
else
    echo "正在启动 Ollama..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 2
    echo "Ollama 已启动"
fi
