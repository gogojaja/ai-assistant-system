#!/bin/bash
# 停止测试环境 1/2/3号 Bot（当前三角色基线，无 4 号文件助手）
echo "正在停止测试环境 1/2/3号 Bot..."

pid=$(lsof -ti:5101 2>/dev/null)
if [ -n "$pid" ]; then
    kill "$pid" 2>/dev/null
    sleep 1
fi

echo "✅ 测试环境 1/2/3号 Bot 已停止"
echo "  当前三角色基线不再保留 4 号文件助手服务。"
