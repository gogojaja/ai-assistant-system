#!/bin/bash
# 停止测试环境 1/2/3号 Bot（不影响 4号）
echo "正在停止测试环境 1/2/3号 Bot..."

pid=$(lsof -ti:5101 2>/dev/null)
if [ -n "$pid" ]; then
    kill "$pid" 2>/dev/null
    sleep 1
fi

echo "✅ 测试环境 1/2/3号 Bot 已停止"
echo "  4号 Bot 不受影响"
